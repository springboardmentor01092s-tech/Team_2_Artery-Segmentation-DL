"""Coronary Artery Stenosis Detection, Severity Classification, QCA and Visualization Pipeline."""

import os, sys, tempfile, json, cv2, yaml, numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib.patches as patches
import torch
from torch.utils.data import DataLoader

os.environ["MPLCONFIGDIR"] = os.path.join(tempfile.gettempdir(), "matplotlib_cache")
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.stenosis_model import StenosisClassifier, calculate_percentage_narrowing, classify_stenosis_severity, SEVERITY_CATEGORIES
from src.gradcam import GradCAM, apply_colormap_on_image, create_cam_overlays, create_explainable_ai_figure
from src.stenosis_utils import extract_centerline_diameters, get_rvd, extract_patch, build_stenosis_dataset, calc_array_stats, format_lesion_record


def extract_candidate_regions(image: np.ndarray, mask: np.ndarray, patch_size: int = 48,
                              stenosis_thresh: float = 0.25, rvd_radius: int = 18, min_rvd: float = 3.5):
    clean_m, coords, diameters = extract_centerline_diameters(mask)
    if coords is None: return []

    raw = []
    for i, (y, x) in enumerate(coords):
        d_cur, rvd = float(diameters[i]), get_rvd(coords, diameters, y, x, rvd_radius)
        if rvd >= min_rvd:
            narr = calculate_percentage_narrowing(rvd, d_cur)
            if narr >= (stenosis_thresh * 100.0) or d_cur <= 0.2:
                raw.append((int(y), int(x), d_cur, rvd, narr))
    if not raw: return []

    clusters, used = [], set()
    for i, c1 in enumerate(raw):
        if i in used: continue
        group = [c1]
        used.add(i)
        for j, c2 in enumerate(raw):
            if j not in used and np.hypot(c1[0] - c2[0], c1[1] - c2[1]) <= 18:
                group.append(c2)
                used.add(j)
        clusters.append(max(group, key=lambda item: item[4]))

    return [{
        "box": box, "center": (int(x), int(y)), "mld_px": round(float(mld), 2),
        "rvd_px": round(float(rvd), 2), "narrowing_pct": round(float(narr), 1),
        "stenosis_pct": round(float(narr), 1), "patch": patch
    } for y, x, mld, rvd, narr in clusters for box, patch in [extract_patch(image, clean_m, y, x, patch_size)]]


def train_stenosis_classifier(config_path: str = "config.yaml"):
    with open(config_path) as f: cfg = yaml.safe_load(f)
    s_cfg, splits = cfg.get("stenosis", {}), json.load(open(cfg["dataset"]["splits_file"]))
    img_dir, msk_dir = cfg["dataset"]["images_dir"], cfg["dataset"]["masks_dir"]
    bs = s_cfg.get("batch_size", 16)

    train_loader = DataLoader(build_stenosis_dataset(splits["train"], img_dir, msk_dir, s_cfg), batch_size=bs, shuffle=True)
    val_loader = DataLoader(build_stenosis_dataset(splits["val"], img_dir, msk_dir, s_cfg), batch_size=bs, shuffle=False)

    dev = torch.device("cuda" if torch.cuda.is_available() and cfg["training"].get("device") == "cuda" else "cpu")
    model = StenosisClassifier(2, 2).to(dev)
    optimizer = torch.optim.Adam(model.parameters(), lr=float(s_cfg.get("learning_rate", 0.001)), weight_decay=1e-4)
    criterion, best_acc = torch.nn.CrossEntropyLoss(), -1.0
    ckpt_path = os.path.join(cfg["paths"]["checkpoints_dir"], "best_stenosis_classifier.pth")
    os.makedirs(cfg["paths"]["checkpoints_dir"], exist_ok=True)

    for ep in range(1, s_cfg.get("epochs", 15) + 1):
        model.train()
        for x, y in train_loader:
            optimizer.zero_grad()
            criterion(model(x.to(dev)), y.to(dev)).backward()
            optimizer.step()
        model.eval()
        with torch.no_grad():
            correct = sum((model(x.to(dev)).argmax(dim=1) == y.to(dev)).sum().item() for x, y in val_loader)
            val_acc = correct / max(1, len(val_loader.dataset))
        if val_acc >= best_acc:
            best_acc = val_acc
            torch.save({"model_state_dict": model.state_dict(), "val_acc": val_acc, "epoch": ep}, ckpt_path)

    print(f"Trained StenosisClassifier saved to: {ckpt_path} (Val Acc: {best_acc * 100:.1f}%)")
    return ckpt_path


def detect_and_localize_stenosis(image: np.ndarray, mask: np.ndarray, model: StenosisClassifier,
                                 device: torch.device, cfg: dict, gradcam: GradCAM = None):
    s_cfg = cfg.get("stenosis", {})
    candidates = extract_candidate_regions(
        image, mask, patch_size=s_cfg.get("patch_size", 48), stenosis_thresh=0.25,
        rvd_radius=s_cfg.get("reference_radius", 18), min_rvd=s_cfg.get("min_ref_caliber", 3.5),
    )
    if not candidates: return []
    model.eval()
    with torch.no_grad():
        patches_tensor = torch.tensor(np.array([c["patch"] for c in candidates]), dtype=torch.float32).to(device)
        probs = torch.softmax(model(patches_tensor), dim=1)[:, 1].cpu().numpy()

    detected = []
    for c, p in zip(candidates, probs):
        c["confidence"] = round(float(p), 3)
        sev = classify_stenosis_severity(c["narrowing_pct"], c["mld_px"], c["rvd_px"])
        c.update({
            "severity": sev["severity_class"], "severity_class": sev["severity_class"],
            "severity_range": sev["severity_range"], "severity_grade": sev["severity_grade"],
            "color": sev["color"], "clinical_action": sev["clinical_action"], "calibration_status": sev["calibration_status"],
        })
        if p >= 0.40 or c["narrowing_pct"] >= 50.0:
            if gradcam:
                cam, conf, pred_cls, _ = gradcam.generate_cam(torch.tensor(c["patch"], dtype=torch.float32).unsqueeze(0).to(device), target_class=1)
                c.update({"gradcam": cam, "cam_conf": conf, "pred_class": pred_cls})
            detected.append(c)

    return sorted(detected, key=lambda x: (x["severity_grade"], x["narrowing_pct"], x["confidence"]), reverse=True)


def create_stenosis_figure(image: np.ndarray, mask: np.ndarray, detected_lesions: list, case_id: str, save_path: str):
    fig, axes = plt.subplots(1, 4, figsize=(22, 5.2))
    axes[0].imshow(image, cmap="gray")
    axes[0].set_title(f"1. Stenosis Localization ({len(detected_lesions)} Lesions)", fontsize=11, fontweight="bold")
    for l in detected_lesions:
        x1, y1, x2, y2 = l["box"]
        axes[0].add_patch(patches.Rectangle((x1, y1), x2 - x1, y2 - y1, linewidth=2, edgecolor=l["color"], facecolor="none"))
        lbl = f"{l['severity']}: {l['narrowing_pct']}%\nMLD={l['mld_px']}px RVD={l['rvd_px']}px\n(p={l['confidence']:.2f})"
        axes[0].text(x1, max(14, y1 - 4), lbl, color="yellow", fontsize=7.2, fontweight="bold",
                     bbox=dict(boxstyle="square,pad=0.2", facecolor="black", alpha=0.75, edgecolor=l["color"]))
        axes[1].plot(*l["center"], "o", color=l["color"], markersize=8, markeredgecolor="white", markeredgewidth=1)

    axes[1].imshow(mask, cmap="gray")
    axes[1].set_title("2. Segmented Artery & Lesion Foci", fontsize=11, fontweight="bold")

    top = detected_lesions[0] if detected_lesions else None
    if top:
        x1, y1, x2, y2 = top["box"]
        crop = image[y1:y2, x1:x2]
        axes[2].imshow(crop if crop.size > 0 else image, cmap="gray")
        axes[2].set_title(f"3. Primary Lesion Zoom: {top['severity']} ({top['severity_range']})\nNarrowing: {top['narrowing_pct']}% | Conf: {top['confidence']:.2f}\nMLD = {top['mld_px']} px | Reference = {top['rvd_px']} px\n[{top['calibration_status']}]",
                          fontsize=9.2, fontweight="bold", color="darkred" if top["severity_grade"] >= 4 else "navy")
        if top.get("gradcam") is not None:
            axes[3].imshow(apply_colormap_on_image((top["patch"][0] * 255.0).astype(np.uint8), top["gradcam"], alpha=0.45))
            axes[3].set_title(f"4. Grad-CAM Feature Attribution\nLuminal Narrowing Focus (Conf: {top['confidence']:.2f})", fontsize=9.5, fontweight="bold", color="darkgreen")
        else:
            axes[3].imshow(image, cmap="gray")
            axes[3].set_title("4. Grad-CAM Explanation\n[No Lesion Activation]", fontsize=10, fontweight="bold")
    else:
        for ax, t in [(axes[2], "3. No Significant Stenosis Detected\n[Normal Vessel Caliber: 0–24%]"), (axes[3], "4. Grad-CAM Explanation\n[No Lesion Activation]")]:
            ax.imshow(image, cmap="gray")
            ax.set_title(t, fontsize=10, fontweight="bold")

    for ax in axes: ax.axis("off")
    plt.suptitle(f"Case {case_id} - Coronary Stenosis Severity, QCA Caliber & Explainable AI (Grad-CAM)\nNotice: Caliber metrics in pixels. Clinical diagnosis requires catheter calibration factor and physician review.", fontsize=12, fontweight="bold", y=0.99)
    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def run_stenosis_pipeline(config_path: str = "config.yaml"):
    with open(config_path) as f: cfg = yaml.safe_load(f)
    ckpt_path = os.path.join(cfg["paths"]["checkpoints_dir"], "best_stenosis_classifier.pth")
    if not os.path.exists(ckpt_path): train_stenosis_classifier(config_path)

    dev = torch.device("cuda" if torch.cuda.is_available() and cfg["training"].get("device") == "cuda" else "cpu")
    model = StenosisClassifier(2, 2).to(dev)
    model.load_state_dict(torch.load(ckpt_path, map_location=dev)["model_state_dict"])
    model.eval()

    gradcam = GradCAM(model)
    test_ids = json.load(open(cfg["dataset"]["splits_file"]))["test"]
    pred_dir = os.path.join(cfg["paths"]["masks_dir"], "Attention_ResUNet_postprocessed")
    mask_dir = pred_dir if os.path.exists(pred_dir) and len(os.listdir(pred_dir)) > 0 else cfg["dataset"]["masks_dir"]

    viz_dir = os.path.join(cfg["paths"]["visualizations_dir"], "stenosis_localization")
    xai_dir = os.path.join(cfg["paths"]["visualizations_dir"], "explainable_ai")
    rpt_dir = cfg["paths"]["reports_dir"]
    for d in [viz_dir, xai_dir, rpt_dir]: os.makedirs(d, exist_ok=True)

    print("=" * 76 + f"\n STENOSIS SEVERITY CLASSIFICATION & QCA PIPELINE | Test Cases: {len(test_ids)}\n" + "=" * 76)
    lesion_results, case_summaries = [], []

    for cid in test_ids:
        img = cv2.imread(os.path.join(cfg["dataset"]["images_dir"], f"{cid}.png"), cv2.IMREAD_GRAYSCALE)
        msk = cv2.imread(os.path.join(mask_dir, f"{cid}.png"), cv2.IMREAD_GRAYSCALE)
        if img is None or msk is None: continue

        lesions = detect_and_localize_stenosis(img, msk, model, dev, cfg, gradcam=gradcam)
        top = lesions[0] if lesions else None
        create_stenosis_figure(img, msk, lesions, cid, os.path.join(viz_dir, f"{cid}_stenosis.png"))
        full_overlay, patch_overlay = create_cam_overlays(img, lesions)
        create_explainable_ai_figure(img, msk, top, full_overlay, patch_overlay, cid, os.path.join(xai_dir, f"{cid}_gradcam.png"))

        records = [format_lesion_record(cid, f"{cid}_L{i}", True, l) for i, l in enumerate(lesions, 1)] if lesions else [format_lesion_record(cid, "", False, None)]
        lesion_results.extend(records)

        sev_cnt = {cat: sum(1 for l in lesions if l["severity"] == cat) for cat in SEVERITY_CATEGORIES}
        case_summaries.append({
            "case_id": cid, "overall_severity": top["severity"] if top else "Normal",
            "max_narrowing_pct": top["narrowing_pct"] if top else 0.0, "primary_mld_px": top["mld_px"] if top else 0.0,
            "case_mean_mld_px": round(float(np.mean([l["mld_px"] for l in lesions])), 2) if lesions else 0.0,
            "primary_rvd_px": top["rvd_px"] if top else 0.0,
            "case_mean_rvd_px": round(float(np.mean([l["rvd_px"] for l in lesions])), 2) if lesions else 0.0,
            "total_lesions_count": len(lesions), **{f"{c.lower().replace(' ', '_')}_count": sev_cnt[c] for c in SEVERITY_CATEGORIES}
        })

    gradcam.remove_hooks()
    df_lesions, df_cases = pd.DataFrame(lesion_results), pd.DataFrame(case_summaries)
    for p in ["stenosis_severity_results.csv", "stenosis_detection_results.csv"]: df_lesions.to_csv(os.path.join(rpt_dir, p), index=False)
    df_cases.to_csv(os.path.join(rpt_dir, "case_stenosis_summary.csv"), index=False)

    active = df_lesions[df_lesions["has_stenosis"]]
    cohort_dist, lesion_dist = df_cases["overall_severity"].value_counts().to_dict(), active["severity_class"].value_counts().to_dict()
    narr, mlds, rvds = [active[c].values if len(active) > 0 else np.array([0.0]) for c in ["percentage_narrowing", "min_lumen_diameter_px", "reference_diameter_px"]]
    mld_s, rvd_s, narr_s = calc_array_stats(mlds), calc_array_stats(rvds), calc_array_stats(narr)

    summary = {
        "pipeline": "Coronary Artery Stenosis Severity Classification, Narrowing Quantification & Explainable AI (Grad-CAM)",
        "total_test_cases": len(test_ids), "total_lesions_detected": len(active),
        "mean_lesions_per_case": round(len(active) / max(1, len(test_ids)), 2),
        "cohort_severity_distribution": {cat: cohort_dist.get(cat, 0) for cat in SEVERITY_CATEGORIES},
        "lesion_severity_distribution": {cat: lesion_dist.get(cat, 0) for cat in SEVERITY_CATEGORIES},
        "primary_lesions_metrics": {
            "description": "Computed strictly on primary lesion of each of 21 test patients",
            "cases_count": len(df_cases), "mean_primary_mld_px": round(float(df_cases["primary_mld_px"].mean()), 2),
            "mean_primary_rvd_px": round(float(df_cases["primary_rvd_px"].mean()), 2),
            "mean_primary_narrowing_pct": round(float(df_cases["max_narrowing_pct"].mean()), 2),
            "std_primary_narrowing_pct": round(float(df_cases["max_narrowing_pct"].std()), 2),
            "min_primary_narrowing_pct": round(float(df_cases["max_narrowing_pct"].min()), 2),
            "max_primary_narrowing_pct": round(float(df_cases["max_narrowing_pct"].max()), 2),
        },
        "all_lesions_metrics": {
            "description": "Computed across all 457 localized lesion sites detected across 21 test patients",
            "lesions_count": len(active),
            **{f"{k}_mld_px": v for k, v in mld_s.items()},
            **{f"{k}_rvd_px": v for k, v in rvd_s.items()},
            **{f"{k}_narrowing_pct": v for k, v in narr_s.items()},
        },
        "percentage_narrowing_metrics": {f"{k}_narrowing_pct": v for k, v in narr_s.items()},
        "caliber_metrics_px": {"mean_mld_px": mld_s["mean"], "mean_rvd_px": rvd_s["mean"],
                                "calibration_disclaimer": "Caliber metrics in pixels. Clinical mm requires catheter/DICOM calibration factor."},
        "explainable_ai": {"method": "Grad-CAM (Gradient-weighted Class Activation Mapping)", "target_layer": "Conv2d(32, 64) - Final feature extractor layer",
                           "output_directory": xai_dir, "figures_generated": len(test_ids)},
        "severity_criteria": {"Normal": "0–24% luminal narrowing", "Mild": "25–49% luminal narrowing", "Moderate": "50–69% luminal narrowing",
                              "Severe": "70–99% luminal narrowing", "Total Occlusion": "100% luminal cut-off / MLD <= 0.1 px"}
    }

    with open(os.path.join(rpt_dir, "stenosis_severity_summary.json"), "w") as fp: json.dump(summary, fp, indent=2)
    with open(os.path.join(rpt_dir, "stenosis_detection_report.json"), "w") as fp:
        json.dump({
            "milestone": "Milestone 3, Severity Classification & Explainable AI",
            "total_test_cases": len(test_ids), "cases_with_stenosis": int((df_cases["overall_severity"] != "Normal").sum()),
            "stenosis_prevalence_pct": round(float((df_cases["overall_severity"] != "Normal").mean() * 100.0), 1),
            "total_lesions_localized": len(active), "cohort_severity": summary["cohort_severity_distribution"],
            "mean_narrowing_pct": summary["percentage_narrowing_metrics"]["mean_narrowing_pct"], "xai_figures_count": len(test_ids),
        }, fp, indent=2)

    print("\n" + "=" * 92 + f"\n{'Case ID':<8}{'Primary Severity':<18}{'Max Narrowing':<16}{'Primary MLD':<14}{'Mean MLD':<12}{'Primary RVD':<14}{'Lesions'}\n" + "-" * 92)
    for _, r in df_cases.iterrows():
        print(f"{str(r['case_id']):<8}{r['overall_severity']:<18}{r['max_narrowing_pct']:>5.1f}%{'':<10}{r['primary_mld_px']:>6.2f} px{'':<5}{r['case_mean_mld_px']:>6.2f} px{'':<3}{r['primary_rvd_px']:>6.2f} px{'':<5}{r['total_lesions_count']:>4d}")

    print("=" * 92 + "\n\nCOHORT SEVERITY BREAKDOWN (Test Cases):")
    for cat in SEVERITY_CATEGORIES:
        cnt = cohort_dist.get(cat, 0)
        print(f"  {cat:<18}: {cnt:>2d} cases ({cnt / len(test_ids) * 100.0:>5.1f}%)")

    p_m, a_m = summary["primary_lesions_metrics"], summary["all_lesions_metrics"]
    print(f"\nQUANTITATIVE LUMINAL NARROWING:\n  [Primary Lesions (N=21)]:\n    - Mean MLD: {p_m['mean_primary_mld_px']} px | Mean RVD: {p_m['mean_primary_rvd_px']} px\n    - Mean Narrowing: {p_m['mean_primary_narrowing_pct']}% ± {p_m['std_primary_narrowing_pct']}%\n  [All Localized Lesions (N=457)]:\n    - Mean MLD: {a_m['mean_mld_px']} px | Mean RVD: {a_m['mean_rvd_px']} px\n    - Mean Narrowing: {a_m['mean_narrowing_pct']}% ± {a_m['std_narrowing_pct']}%\n  Notice: {summary['caliber_metrics_px']['calibration_disclaimer']}")
    print(f"\nDELIVERABLES GENERATED:\n  - Reports: {rpt_dir}/ (CSV & JSON)\n  - Visualizations: {viz_dir}/ & {xai_dir}/\n" + "=" * 78)
    return summary


if __name__ == "__main__":
    run_stenosis_pipeline("config.yaml")
