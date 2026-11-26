"""Model Comparison and Statistical Profiling for CoroVision-AI."""

import os, sys, tempfile, time, json, yaml, numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import ttest_rel
import torch

os.environ["MPLCONFIGDIR"] = os.path.join(tempfile.gettempdir(), "matplotlib_cache")
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.unet import BaselineUNet
from models.attention_resunet import AttentionResUNet


def measure_model_efficiency(model: torch.nn.Module, device: torch.device, input_shape=(1, 1, 320, 320), runs: int = 25):
    model.eval().to(device)
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

    dummy = torch.randn(*input_shape).to(device)
    with torch.no_grad():
        for _ in range(5):
            _ = model(dummy)
    if device.type == "cuda":
        torch.cuda.synchronize()

    start = time.perf_counter()
    with torch.no_grad():
        for _ in range(runs):
            _ = model(dummy)
            if device.type == "cuda":
                torch.cuda.synchronize()
    elapsed = time.perf_counter() - start
    avg_latency_ms = (elapsed / runs) * 1000.0
    fps = 1000.0 / avg_latency_ms if avg_latency_ms > 0 else 0.0

    return {
        "total_parameters": int(total_params),
        "trainable_parameters": int(trainable_params),
        "avg_latency_ms": round(float(avg_latency_ms), 2),
        "fps": round(float(fps), 1),
    }


def generate_comparison_figure(metrics_summary: dict, df_results: pd.DataFrame, df_vessel: pd.DataFrame, save_path: str):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    w = 0.35

    # Panel 1: Core Metrics Bar Chart
    metric_names = ["Dice (F1)", "IoU", "Precision", "Recall", "Specificity"]
    keys = ["mean_dice", "mean_iou", "mean_precision", "mean_recall", "mean_specificity"]
    u_vals = [metrics_summary["Baseline_UNet"][k] for k in keys]
    a_vals = [metrics_summary["Attention_ResUNet"][k] for k in keys]
    x = np.arange(len(metric_names))

    axes[0, 0].bar(x - w/2, u_vals, w, label="Baseline U-Net", color="#4285F4", edgecolor="black", alpha=0.9)
    axes[0, 0].bar(x + w/2, a_vals, w, label="Attention ResU-Net", color="#0F9D58", edgecolor="black", alpha=0.9)
    axes[0, 0].set_ylabel("Score (0.0 - 1.0)", fontweight="bold")
    axes[0, 0].set_title("1. Segmentation Metrics (Mean)", fontsize=11, fontweight="bold")
    axes[0, 0].set_xticks(x)
    axes[0, 0].set_xticklabels(metric_names, fontsize=9, fontweight="bold")
    axes[0, 0].set_ylim([0.5, 1.05])
    axes[0, 0].grid(axis="y", linestyle=":", alpha=0.6)
    axes[0, 0].legend(loc="lower right")

    # Panel 2: Case-wise Dice Score Distribution Boxplot
    u_dices = df_results[df_results["model"] == "Baseline_UNet"]["dice"].values
    a_dices = df_results[df_results["model"] == "Attention_ResUNet"]["dice"].values
    bp = axes[0, 1].boxplot([u_dices, a_dices], tick_labels=["Baseline U-Net", "Attention ResU-Net"], patch_artist=True)
    bp["boxes"][0].set_facecolor("#4285F4")
    bp["boxes"][1].set_facecolor("#0F9D58")
    axes[0, 1].set_ylabel("Dice Score", fontweight="bold")
    axes[0, 1].set_title("2. Test Case Dice Distribution (N=21)", fontsize=11, fontweight="bold")
    axes[0, 1].grid(axis="y", linestyle=":", alpha=0.6)

    # Panel 3: Vessel Morphometry Comparison
    u_len = df_vessel[df_vessel["model"] == "Baseline_UNet"]["centerline_length_px"].mean()
    a_len = df_vessel[df_vessel["model"] == "Attention_ResUNet"]["centerline_length_px"].mean()
    u_dia = df_vessel[df_vessel["model"] == "Baseline_UNet"]["mean_diameter_px"].mean()
    a_dia = df_vessel[df_vessel["model"] == "Attention_ResUNet"]["mean_diameter_px"].mean()

    m_names = ["Centerline Length (px / 100)", "Mean Caliber (px)"]
    m_u = [u_len / 100.0, u_dia]
    m_a = [a_len / 100.0, a_dia]
    x_m = np.arange(len(m_names))
    axes[1, 0].bar(x_m - w/2, m_u, w, label="Baseline U-Net", color="#4285F4", edgecolor="black", alpha=0.9)
    axes[1, 0].bar(x_m + w/2, m_a, w, label="Attention ResU-Net", color="#0F9D58", edgecolor="black", alpha=0.9)
    axes[1, 0].set_title("3. Vascular Morphometry Recovery", fontsize=11, fontweight="bold")
    axes[1, 0].set_xticks(x_m)
    axes[1, 0].set_xticklabels(m_names, fontsize=9, fontweight="bold")
    axes[1, 0].grid(axis="y", linestyle=":", alpha=0.6)
    axes[1, 0].legend()

    # Panel 4: Efficiency (Parameters & Latency)
    eff_names = ["Parameters (M)", "Latency (ms)"]
    eff_u = [metrics_summary["Baseline_UNet"]["total_parameters"] / 1e6, metrics_summary["Baseline_UNet"]["avg_latency_ms"]]
    eff_a = [metrics_summary["Attention_ResUNet"]["total_parameters"] / 1e6, metrics_summary["Attention_ResUNet"]["avg_latency_ms"]]
    x_e = np.arange(len(eff_names))
    axes[1, 1].bar(x_e - w/2, eff_u, w, label="Baseline U-Net", color="#4285F4", edgecolor="black", alpha=0.9)
    axes[1, 1].bar(x_e + w/2, eff_a, w, label="Attention ResU-Net", color="#0F9D58", edgecolor="black", alpha=0.9)
    axes[1, 1].set_title("4. Model Complexity & Latency", fontsize=11, fontweight="bold")
    axes[1, 1].set_xticks(x_e)
    axes[1, 1].set_xticklabels(eff_names, fontsize=9, fontweight="bold")
    axes[1, 1].grid(axis="y", linestyle=":", alpha=0.6)
    axes[1, 1].legend()

    plt.suptitle("CoroVision-AI Architecture Benchmarking: Baseline U-Net vs Attention ResU-Net", fontsize=13, fontweight="bold", y=0.99)
    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def compare_models(config_path: str = "config.yaml") -> dict:
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    rpt_dir = cfg["paths"]["reports_dir"]
    ckpt_dir = cfg["paths"]["checkpoints_dir"]
    results_csv = os.path.join(rpt_dir, "results.csv")
    vessel_csv = os.path.join(rpt_dir, "vessel_analysis.csv")

    if not os.path.exists(results_csv) or not os.path.exists(vessel_csv):
        from src.evaluate import evaluate_both_models
        evaluate_both_models(config_path)

    df_results = pd.read_csv(results_csv)
    df_vessel = pd.read_csv(vessel_csv)

    dev_str = cfg["training"].get("device", "cuda")
    device = torch.device(dev_str if (torch.cuda.is_available() and dev_str == "cuda") else "cpu")

    in_ch, num_cls = cfg["dataset"].get("in_channels", 1), cfg["dataset"].get("num_classes", 1)
    u_model = BaselineUNet(in_ch, num_cls, cfg["models"]["baseline_unet"].get("features", [32, 64, 128, 256, 512]))
    a_model = AttentionResUNet(in_ch, num_cls, cfg["models"]["attention_resunet"].get("features", [32, 64, 128, 256, 512]))

    u_eff = measure_model_efficiency(u_model, device)
    a_eff = measure_model_efficiency(a_model, device)

    u_ckpt = os.path.join(ckpt_dir, "best_Baseline_UNet.pth")
    a_ckpt = os.path.join(ckpt_dir, "best_Attention_ResUNet.pth")
    u_eff["checkpoint_size_mb"] = round(os.path.getsize(u_ckpt) / (1024 * 1024), 2) if os.path.exists(u_ckpt) else 0.0
    a_eff["checkpoint_size_mb"] = round(os.path.getsize(a_ckpt) / (1024 * 1024), 2) if os.path.exists(a_ckpt) else 0.0

    u_df = df_results[df_results["model"] == "Baseline_UNet"].sort_values("case_id").reset_index(drop=True)
    a_df = df_results[df_results["model"] == "Attention_ResUNet"].sort_values("case_id").reset_index(drop=True)

    metrics_list = ["dice", "iou", "precision", "recall", "specificity"]
    comparison_table = []
    comparison_dict = {}

    for m in metrics_list:
        u_vals, a_vals = u_df[m].values, a_df[m].values
        u_mean, u_std = float(np.mean(u_vals)), float(np.std(u_vals))
        a_mean, a_std = float(np.mean(a_vals)), float(np.std(a_vals))
        delta = a_mean - u_mean
        gain_pct = (delta / (u_mean + 1e-6)) * 100.0

        t_stat, p_val = ttest_rel(a_vals, u_vals)

        comparison_table.append({
            "metric": m.upper() if m in ["iou", "dice"] else m.capitalize(),
            "baseline_unet": f"{u_mean:.4f} ± {u_std:.4f}",
            "attention_resunet": f"{a_mean:.4f} ± {a_std:.4f}",
            "absolute_delta": f"{'+' if delta >= 0 else ''}{delta:.4f}",
            "relative_gain": f"{'+' if gain_pct >= 0 else ''}{gain_pct:.2f}%",
            "p_value": round(float(p_val), 4),
            "statistically_significant": bool(p_val < 0.05),
        })

        comparison_dict[m] = {
            "baseline_mean": round(u_mean, 4), "baseline_std": round(u_std, 4),
            "attention_mean": round(a_mean, 4), "attention_std": round(a_std, 4),
            "delta": round(delta, 4), "gain_pct": round(gain_pct, 2),
            "p_value": round(float(p_val), 4),
            "significant": bool(p_val < 0.05),
        }

    u_v = df_vessel[df_vessel["model"] == "Baseline_UNet"]
    a_v = df_vessel[df_vessel["model"] == "Attention_ResUNet"]
    morph_comparison = {
        "mean_centerline_length_px": {
            "baseline": round(float(u_v["centerline_length_px"].mean()), 1),
            "attention": round(float(a_v["centerline_length_px"].mean()), 1),
            "gain_px": round(float(a_v["centerline_length_px"].mean() - u_v["centerline_length_px"].mean()), 1),
        },
        "mean_vessel_diameter_px": {
            "baseline": round(float(u_v["mean_diameter_px"].mean()), 2),
            "attention": round(float(a_v["mean_diameter_px"].mean()), 2),
        }
    }

    full_summary = {
        "task": "Coronary Artery Segmentation Model Comparison",
        "test_cases": len(u_df),
        "device": str(device),
        "metrics_comparison": comparison_dict,
        "morphometry_comparison": morph_comparison,
        "efficiency": {"Baseline_UNet": u_eff, "Attention_ResUNet": a_eff},
        "comparison_table": comparison_table,
    }

    metrics_for_fig = {
        "Baseline_UNet": {f"mean_{m}": comparison_dict[m]["baseline_mean"] for m in metrics_list},
        "Attention_ResUNet": {f"mean_{m}": comparison_dict[m]["attention_mean"] for m in metrics_list},
    }
    metrics_for_fig["Baseline_UNet"].update(u_eff)
    metrics_for_fig["Attention_ResUNet"].update(a_eff)
    chart_path = os.path.join(rpt_dir, "model_comparison.png")
    generate_comparison_figure(metrics_for_fig, df_results, df_vessel, chart_path)

    pd.DataFrame(comparison_table).to_csv(os.path.join(rpt_dir, "model_comparison.csv"), index=False)
    with open(os.path.join(rpt_dir, "model_comparison.json"), "w") as f:
        json.dump(full_summary, f, indent=2)

    md_path = os.path.join(rpt_dir, "model_comparison_report.md")
    rows_md = "\n".join(f"| **{r['metric']}** | {r['baseline_unet']} | {r['attention_resunet']} | {r['absolute_delta']} | {r['relative_gain']} | {r['p_value']:.4f} | {'Yes' if r['statistically_significant'] else 'No'} |" for r in comparison_table)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# CoroVision-AI: Architecture Comparison Report\n\nEvaluated on **{len(u_df)}** held-out test angiograms from the DCA/ICA dataset.\n\n### 1. Segmentation Performance & Statistical Significance\n\n| Metric | Baseline U-Net | Attention ResU-Net | Absolute Delta | Relative Gain | p-value | Significant (p<0.05) |\n| :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n{rows_md}\n\n### 2. Computational Efficiency & Complexity\n\n- **Baseline U-Net**: {u_eff['total_parameters']:,} params ({u_eff['checkpoint_size_mb']} MB) | Latency: {u_eff['avg_latency_ms']} ms ({u_eff['fps']} FPS)\n- **Attention ResU-Net**: {a_eff['total_parameters']:,} params ({a_eff['checkpoint_size_mb']} MB) | Latency: {a_eff['avg_latency_ms']} ms ({a_eff['fps']} FPS)\n\n### 3. Vessel Morphometry Recovery\n\n- **Centerline Length**: Baseline = {morph_comparison['mean_centerline_length_px']['baseline']} px vs Attention = {morph_comparison['mean_centerline_length_px']['attention']} px (+{morph_comparison['mean_centerline_length_px']['gain_px']} px)\n- **Mean Caliber**: Baseline = {morph_comparison['mean_vessel_diameter_px']['baseline']} px vs Attention = {morph_comparison['mean_vessel_diameter_px']['attention']} px\n")

    print("\n" + "=" * 80 + "\n MODEL COMPARISON SUMMARY (Baseline U-Net vs Attention ResU-Net)\n" + "=" * 80)
    for r in comparison_table:
        print(f"  {r['metric']:<12}: Baseline={r['baseline_unet']} | Attention={r['attention_resunet']} | Gain={r['relative_gain']} (p={r['p_value']})")
    print(f"  Centerline  : Baseline={morph_comparison['mean_centerline_length_px']['baseline']} px | Attention={morph_comparison['mean_centerline_length_px']['attention']} px (+{morph_comparison['mean_centerline_length_px']['gain_px']} px)")
    print(f"  Inference   : Baseline={u_eff['avg_latency_ms']} ms ({u_eff['fps']} FPS) | Attention={a_eff['avg_latency_ms']} ms ({a_eff['fps']} FPS)\n" + "=" * 80)

    return full_summary


if __name__ == "__main__":
    compare_models("config.yaml")
