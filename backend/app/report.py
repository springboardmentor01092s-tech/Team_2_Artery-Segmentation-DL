"""Builds the case report (PDF / CSV / JSON) covering the whole workflow."""
import csv
import io
import os
from datetime import datetime, timezone
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    CondPageBreak,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

DISCLAIMER = (
    "This report was produced by a research prototype. The findings are model "
    "estimates and are not a clinical diagnosis. They must be reviewed by a "
    "qualified clinician."
)


# ---------------------------------------------------------------- helpers
def _v(x, suffix=""):
    return "-" if x is None or x == "" else f"{x}{suffix}"


def _pct(x):
    return "-" if x is None else f"{x * 100:.1f}%"


def _num(x):
    if x is None or x == "":
        return "-"
    if isinstance(x, (int, float)):
        return f"{x:.3f}"
    return str(x)


def _local_path(url):
    """'/uploads/results/a.png?t=1' -> 'uploads/results/a.png' (if the file exists)."""
    if not url:
        return None
    p = str(url).split("?")[0].lstrip("/")
    return p if os.path.exists(p) else None


def explain_text(c):
    parts = []
    score = c.get("score")
    if score is not None:
        parts.append(f"The classifier is {score * 100:.1f}% confident that this region is a stenosis.")
    n = c.get("narrowing_pct")
    if n is not None and n >= 5:
        parts.append(
            f"The vessel narrows to {c.get('narrowest_width_px')}px where the normal width nearby is "
            f"{c.get('reference_width_px')}px, an estimated {n}% narrowing ({c.get('severity')})."
        )
    elif n is not None:
        parts.append(
            "No measurable narrowing was found in the vessel width here. The model flagged this "
            "region from its appearance, so it is worth a closer look."
        )
    if c.get("location"):
        seg = f", on vessel segment {c.get('segment')}" if c.get("segment") else ""
        parts.append(f"It is located in the {c.get('location')} of the image{seg}.")
    return " ".join(parts)


# ---------------------------------------------------------------- data
def build_report_data(
    case, pipeline, metrics, generated_by,
    preprocessing=None, history=None, comparison=None,
):
    """Merge everything about one case into a single dict."""
    cands = pipeline.get("candidates") or []
    regions = []
    for i, c in enumerate(cands, 1):
        regions.append(
            {
                "no": i,
                "score": c.get("score"),
                "location": c.get("location"),
                "segment": c.get("segment"),
                "vessel_width_px": c.get("local_diameter_px"),
                "narrowest_width_px": c.get("narrowest_width_px"),
                "reference_width_px": c.get("reference_width_px"),
                "narrowing_pct": c.get("narrowing_pct"),
                "severity": c.get("severity"),
                "bbox": c.get("bbox"),
                "explanation": explain_text(c),
                "gradcam_url": c.get("gradcam_url"),
            }
        )

    with_narrowing = [r for r in regions if r["narrowing_pct"] is not None]
    worst = max(with_narrowing, key=lambda r: r["narrowing_pct"]) if with_narrowing else None

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "generated_by": generated_by,
        "patient": {
            "patient_id": case.patient_id,
            "age": case.age,
            "gender": case.gender,
            "imaging_modality": case.imaging_modality,
            "scan_date": case.scan_date,
            "anatomical_region": case.anatomical_region,
            "analysis_status": case.analysis_status,
            "model_version": case.model_version,
            "medical_history": case.medical_history,
            "risk_factors": case.risk_factors,
            "clinical_notes": case.clinical_notes,
        },
        "preprocessing": preprocessing or [],
        "vessel_analysis": pipeline.get("vessel_stats") or {},
        "summary": {
            "regions_flagged": len(regions),
            "highest_narrowing_pct": worst["narrowing_pct"] if worst else None,
            "highest_severity": worst["severity"] if worst else None,
        },
        "stenosis_regions": regions,
        "model_comparison": comparison,
        "classifier_performance": metrics,
        "history": history or [],
        "images": {
            "visualization": pipeline.get("visualization_url"),
            "vessel_mask": pipeline.get("vessel_mask_url"),
            "centerline": pipeline.get("centerline_url"),
            "stenosis_mask": pipeline.get("stenosis_mask_url"),
        },
        "disclaimer": DISCLAIMER,
    }


# ---------------------------------------------------------------- CSV
def build_csv(data):
    p = data["patient"]
    header = [
        "patient_id", "age", "gender", "scan_date", "artery_region", "status", "model_version",
        "stenosis_no", "score", "location", "segment", "vessel_width_px",
        "narrowest_width_px", "reference_width_px", "narrowing_pct", "severity", "bbox",
    ]
    base = [
        p["patient_id"], p["age"], p["gender"], p["scan_date"], p["anatomical_region"],
        p["analysis_status"], p["model_version"],
    ]
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(header)
    regions = data["stenosis_regions"]
    if not regions:
        w.writerow(base + ["", "", "", "", "", "", "", "", "No stenosis candidates", ""])
    for r in regions:
        w.writerow(
            base
            + [
                r["no"], r["score"], r["location"], r["segment"], r["vessel_width_px"],
                r["narrowest_width_px"], r["reference_width_px"], r["narrowing_pct"],
                r["severity"], " ".join(str(x) for x in (r["bbox"] or [])),
            ]
        )
    return out.getvalue()


# ---------------------------------------------------------------- PDF
def _image(path, max_w, max_h):
    iw, ih = ImageReader(path).getSize()
    scale = min(max_w / iw, max_h / ih)
    return Image(path, width=iw * scale, height=ih * scale)


def _table(rows, widths, header=True):
    t = Table(rows, colWidths=widths, repeatRows=1 if header else 0)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")))
    else:
        style.append(("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")))
    t.setStyle(TableStyle(style))
    return t


def _image_grid(items, per_row, img_w, img_h, caption_style):
    """items: list of (label, local_path). Returns a Table of images with captions."""
    rows, row = [], []
    for label, path in items:
        row.append([_image(path, img_w, img_h), Paragraph(escape(label), caption_style)])
        if len(row) == per_row:
            rows.append(row)
            row = []
    if row:
        row += [""] * (per_row - len(row))
        rows.append(row)
    t = Table(rows, colWidths=[17 * cm / per_row] * per_row)
    t.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return t


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.drawString(2 * cm, 1 * cm, "Artery AI - research prototype, not for clinical diagnosis")
    canvas.drawRightString(A4[0] - 2 * cm, 1 * cm, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf(data):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=1.8 * cm, bottomMargin=1.8 * cm,
        title="Coronary Artery Analysis Report",
    )
    ss = getSampleStyleSheet()
    title = ParagraphStyle("t", parent=ss["Title"], fontSize=18, spaceAfter=4)
    h2 = ParagraphStyle(
        "h2", parent=ss["Heading2"], fontSize=12, spaceBefore=12, spaceAfter=6,
        textColor=colors.HexColor("#1e293b"),
    )
    body = ParagraphStyle("b", parent=ss["BodyText"], fontSize=9, leading=12)
    small = ParagraphStyle("s", parent=body, fontSize=8, leading=10, textColor=colors.HexColor("#64748b"))
    caption = ParagraphStyle("cap", parent=small, alignment=1)
    cell = ParagraphStyle("c", parent=body, fontSize=8.5, leading=11)
    cell_b = ParagraphStyle("cb", parent=cell, fontName="Helvetica-Bold")
    head = ParagraphStyle("hd", parent=cell, fontName="Helvetica-Bold", textColor=colors.white)

    def P(text, style=cell):
        return Paragraph(escape(str(text)), style)

    def H(text):
        """Section heading that never ends up alone at the bottom of a page."""
        return [CondPageBreak(5 * cm), Paragraph(escape(text), h2)]

    story = [
        Paragraph("Coronary Artery Analysis Report", title),
        Paragraph(escape(f"Generated {data['generated_at']} by {data['generated_by']}"), small),
        Spacer(1, 6),
    ]

    # 1. patient and case details
    p = data["patient"]
    story += H("1. Patient and case details")
    rows = [
        ("Patient ID", p["patient_id"]),
        ("Age / Gender", f"{_v(p['age'])} / {_v(p['gender'])}"),
        ("Imaging modality", _v(p["imaging_modality"])),
        ("Scan date", _v(p["scan_date"])),
        ("Artery region", _v(p["anatomical_region"])),
        ("Analysis status", _v(p["analysis_status"])),
        ("Model version", _v(p["model_version"])),
        ("Medical history", _v(p["medical_history"])),
        ("Risk factors", _v(p["risk_factors"])),
        ("Clinical notes", _v(p["clinical_notes"])),
    ]
    story.append(_table([[P(k, cell_b), P(v)] for k, v in rows], [4.5 * cm, 12.5 * cm], header=False))

    # 2. summary
    s = data["summary"]
    story += H("2. Summary")
    if s["regions_flagged"] == 0:
        story.append(Paragraph("No suspected stenosis regions were flagged.", body))
    else:
        text = f"{s['regions_flagged']} suspected stenosis region(s) flagged."
        if s["highest_narrowing_pct"] is not None:
            text += (
                f" Highest estimated narrowing: {s['highest_narrowing_pct']}% "
                f"({_v(s['highest_severity'])})."
            )
        story.append(Paragraph(escape(text), body))

    # 3. scan and preprocessing
    pre = []
    for item in data.get("preprocessing") or []:
        path = _local_path(item.get("url"))
        if path:
            pre.append((item["name"], path))
    if pre:
        story += H("3. Scan and preprocessing")
        story.append(
            Paragraph(
                "The uploaded scan and each preprocessing stage: normalization, noise reduction, "
                "contrast enhancement, region of interest and model input.",
                small,
            )
        )
        story.append(Spacer(1, 4))
        story.append(_image_grid(pre, 3, 5.2 * cm, 5.2 * cm, caption))

    # 4. artery segmentation
    seg_items = []
    for label, key in [("Vessel mask", "vessel_mask"), ("Centerline", "centerline")]:
        path = _local_path(data["images"].get(key))
        if path:
            seg_items.append((label, path))
    v = data["vessel_analysis"]
    if seg_items or v:
        story += H("4. Artery segmentation and vessel analysis")
        if seg_items:
            story.append(_image_grid(seg_items, 2, 7.5 * cm, 7.5 * cm, caption))
        if v:
            vrows = [
                ("Vessel segments", _v(v.get("vessel_segments"))),
                ("Centerline length", _v(v.get("centerline_length_px"), " px")),
                ("Mean diameter", _v(v.get("mean_diameter_px"), " px")),
                ("Max diameter", _v(v.get("max_diameter_px"), " px")),
                ("Min diameter", _v(v.get("min_diameter_px"), " px")),
            ]
            story.append(_table([[P(k, cell_b), P(x)] for k, x in vrows], [4.5 * cm, 12.5 * cm], header=False))

    # 5. stenosis findings
    regions = data["stenosis_regions"]
    story += H("5. Stenosis findings")
    if regions:
        trows = [[P(h, head) for h in ["#", "Score", "Location", "Segment", "Vessel width", "Narrowing", "Severity"]]]
        for r in regions:
            trows.append(
                [
                    P(r["no"]), P(_v(r["score"])), P(_v(r["location"])), P(_v(r["segment"])),
                    P(_v(r["vessel_width_px"], " px")), P(_v(r["narrowing_pct"], "%")),
                    P(_v(r["severity"])),
                ]
            )
        story.append(_table(trows, [1 * cm, 2 * cm, 3 * cm, 2.5 * cm, 3 * cm, 2.5 * cm, 3 * cm]))
    else:
        story.append(Paragraph("No candidate regions found.", body))

    vis = _local_path(data["images"].get("visualization"))
    if vis:
        story.append(Spacer(1, 8))
        story.append(
            Paragraph("Original scan, artery segmentation, stenosis regions and model explanation.", small)
        )
        story.append(Spacer(1, 4))
        story.append(_image(vis, 17 * cm, 12 * cm))

    if regions:
        story += H("Why each region was flagged")
        for r in regions:
            story.append(Paragraph(escape(f"Region {r['no']}"), cell_b))
            story.append(Paragraph(escape(r["explanation"]), body))
            gc = _local_path(r.get("gradcam_url"))
            if gc:
                story.append(Spacer(1, 3))
                story.append(_image(gc, 12 * cm, 4 * cm))
                story.append(
                    Paragraph("Panels: crop, Grad-CAM, Grad-CAM++. Red marks where the model focused most.", small)
                )
            story.append(Spacer(1, 8))

    # 6. model comparison (only when weights/model_comparison.json exists)
    comp = data.get("model_comparison")
    if comp and comp.get("models"):
        story += H("6. Model comparison")
        crow = [[P(h, head) for h in ["Model", "Dice", "IoU", "Precision", "Recall"]]]
        for m in comp["models"]:
            crow.append(
                [P(m.get("name", "-")), P(_num(m.get("dice"))), P(_num(m.get("iou"))),
                 P(_num(m.get("precision"))), P(_num(m.get("recall")))]
            )
        story.append(_table(crow, [5 * cm, 3 * cm, 3 * cm, 3 * cm, 3 * cm]))
        if comp.get("note"):
            story.append(Spacer(1, 3))
            story.append(Paragraph(escape(str(comp["note"])), small))

    # 7. classifier performance
    m = data.get("classifier_performance")
    if m:
        story += H("7. Stenosis classifier performance (test set)")
        f1 = m.get("f1")
        auc = m.get("auc")
        mrows = [
            ("Accuracy", _pct(m.get("accuracy"))),
            ("Precision", _pct(m.get("precision"))),
            ("Sensitivity (recall)", _pct(m.get("recall"))),
            ("Specificity", _pct(m.get("specificity"))),
            ("F1-score", "-" if f1 is None else f"{f1:.3f}"),
            ("AUC-ROC", "-" if auc is None else f"{auc:.3f}"),
            (
                "Confusion matrix",
                f"TP {_v(m.get('tp'))}, FP {_v(m.get('fp'))}, TN {_v(m.get('tn'))}, FN {_v(m.get('fn'))}",
            ),
        ]
        story.append(_table([[P(k, cell_b), P(x)] for k, x in mrows], [4.5 * cm, 12.5 * cm], header=False))

    # 8. processing history
    hist = data.get("history") or []
    if hist:
        story += H("8. Processing history")
        hrows = [[P(h, head) for h in ["Time", "User", "Role", "Action", "Detail"]]]
        for h in hist:
            hrows.append(
                [P(h.get("time")), P(h.get("user")), P(h.get("role")),
                 P(str(h.get("action", "")).replace("_", " ")), P(h.get("detail"))]
            )
        story.append(_table(hrows, [3.2 * cm, 2.6 * cm, 2.4 * cm, 3.3 * cm, 5.5 * cm]))

    story.append(Spacer(1, 14))
    story.append(Paragraph(escape(data["disclaimer"]), small))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()