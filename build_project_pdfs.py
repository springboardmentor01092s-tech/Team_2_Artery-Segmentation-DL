from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output" / "pdf"
OUT.mkdir(parents=True, exist_ok=True)

NAVY = colors.HexColor("#12304A")
BLUE = colors.HexColor("#1876A3")
TEAL = colors.HexColor("#16A6A1")
PALE = colors.HexColor("#EAF5F7")
INK = colors.HexColor("#243746")
MUTED = colors.HexColor("#647783")
LINE = colors.HexColor("#CFDFE5")
WHITE = colors.white


def register_fonts():
    regular = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
    bold = Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf")
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("ProjectSans", str(regular)))
        pdfmetrics.registerFont(TTFont("ProjectSans-Bold", str(bold)))
        return "ProjectSans", "ProjectSans-Bold"
    return "Helvetica", "Helvetica-Bold"


FONT, FONT_BOLD = register_fonts()


class StepFlow(Flowable):
    def __init__(self, steps, width=170 * mm, box_h=20 * mm, gap=5 * mm):
        super().__init__()
        self.steps = steps
        self.width = width
        self.box_h = box_h
        self.gap = gap
        self.height = len(steps) * box_h + (len(steps) - 1) * gap

    def draw(self):
        canvas = self.canv
        for index, (title, detail) in enumerate(self.steps):
            y = self.height - (index + 1) * self.box_h - index * self.gap
            canvas.setFillColor(PALE if index % 2 == 0 else colors.HexColor("#F4F8FA"))
            canvas.setStrokeColor(TEAL)
            canvas.setLineWidth(1)
            canvas.roundRect(0, y, self.width, self.box_h, 3 * mm, fill=1, stroke=1)
            canvas.setFillColor(TEAL)
            canvas.circle(8 * mm, y + self.box_h / 2, 4 * mm, fill=1, stroke=0)
            canvas.setFillColor(WHITE)
            canvas.setFont(FONT_BOLD, 9)
            canvas.drawCentredString(8 * mm, y + self.box_h / 2 - 3, str(index + 1))
            canvas.setFillColor(NAVY)
            canvas.setFont(FONT_BOLD, 9.5)
            canvas.drawString(16 * mm, y + self.box_h - 5 * mm, title)
            canvas.setFillColor(INK)
            canvas.setFont(FONT, 8)
            canvas.drawString(16 * mm, y + 3.2 * mm, detail)
            if index < len(self.steps) - 1:
                center = self.width / 2
                canvas.setStrokeColor(TEAL)
                canvas.setLineWidth(1.3)
                canvas.line(center, y, center, y - self.gap + 2 * mm)
                canvas.line(center, y - self.gap + 2 * mm, center - 2 * mm, y - self.gap + 5 * mm)
                canvas.line(center, y - self.gap + 2 * mm, center + 2 * mm, y - self.gap + 5 * mm)


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=base["Title"], fontName=FONT_BOLD, fontSize=24, leading=29, textColor=NAVY, alignment=TA_LEFT, spaceAfter=7 * mm),
        "subtitle": ParagraphStyle("subtitle", parent=base["Normal"], fontName=FONT, fontSize=11, leading=16, textColor=MUTED, spaceAfter=8 * mm),
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName=FONT_BOLD, fontSize=16, leading=20, textColor=NAVY, spaceBefore=4 * mm, spaceAfter=4 * mm),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName=FONT_BOLD, fontSize=11, leading=14, textColor=BLUE, spaceBefore=2 * mm, spaceAfter=2 * mm),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontName=FONT, fontSize=9.5, leading=14, textColor=INK, spaceAfter=3 * mm),
        "small": ParagraphStyle("small", parent=base["BodyText"], fontName=FONT, fontSize=8, leading=11, textColor=MUTED),
        "callout": ParagraphStyle("callout", parent=base["BodyText"], fontName=FONT, fontSize=10, leading=15, textColor=NAVY, leftIndent=5 * mm, rightIndent=5 * mm, spaceBefore=3 * mm, spaceAfter=3 * mm),
        "center": ParagraphStyle("center", parent=base["BodyText"], fontName=FONT_BOLD, fontSize=9, leading=12, textColor=NAVY, alignment=TA_CENTER),
    }


S = styles()


def header_footer(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, height - 12 * mm, width, 12 * mm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont(FONT_BOLD, 8)
    canvas.drawString(20 * mm, height - 7.7 * mm, "ARTERY SEGMENTATION & STENOSIS DETECTION")
    canvas.setStrokeColor(LINE)
    canvas.line(20 * mm, 14 * mm, width - 20 * mm, 14 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont(FONT, 8)
    canvas.drawString(20 * mm, 9 * mm, "Advanced Deep Learning Techniques")
    canvas.drawRightString(width - 20 * mm, 9 * mm, f"Page {doc.page}")
    canvas.restoreState()


def make_doc(path, title):
    frame = Frame(20 * mm, 18 * mm, A4[0] - 40 * mm, A4[1] - 36 * mm, topPadding=10 * mm, bottomPadding=5 * mm, id="main")
    template = PageTemplate(id="main", frames=[frame], onPageEnd=header_footer)
    doc = BaseDocTemplate(str(path), pagesize=A4, title=title, author="Project Team", subject="Artery segmentation and stenosis detection")
    doc.addPageTemplates([template])
    return doc


def pill(text):
    table = Table([[Paragraph(text, S["center"])]], colWidths=[55 * mm], rowHeights=[10 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE),
        ("BOX", (0, 0), (-1, -1), 0.8, TEAL),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
    ]))
    return table


def project_documentation():
    path = OUT / "project_documentation.pdf"
    doc = make_doc(path, "Project Documentation")
    story = [
        Spacer(1, 10 * mm),
        Paragraph("Project Documentation", S["subtitle"]),
        Paragraph("Artery Segmentation and Stenosis Detection using Advanced Deep Learning Techniques", S["title"]),
        Paragraph("A structured technical overview of an AI-assisted pipeline for extracting arterial anatomy and identifying clinically relevant narrowing in medical images.", S["subtitle"]),
        Table([[pill("Medical Image Analysis"), pill("Deep Learning"), pill("Clinical Decision Support")]], colWidths=[57 * mm] * 3, style=[("VALIGN", (0, 0), (-1, -1), "TOP")]),
        Spacer(1, 10 * mm),
        Paragraph("Objective", S["h1"]),
        Paragraph("The objective is to develop an automated deep learning system that segments arteries from medical images and detects potential stenosis. The system is intended to produce accurate vessel masks, estimate the degree and location of narrowing, and present interpretable outputs that can support clinical review.", S["body"]),
        Table([[Paragraph("PRIMARY GOAL", S["center"]), Paragraph("EXPECTED OUTPUT", S["center"])], [Paragraph("Reliable artery extraction despite variations in image quality, vessel size, and anatomy.", S["body"]), Paragraph("A vessel segmentation mask, suspected stenosis location, severity estimate, and visual overlay.", S["body"])]], colWidths=[85 * mm, 85 * mm], style=[("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), WHITE), ("GRID", (0, 0), (-1, -1), 0.6, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm), ("TOPPADDING", (0, 0), (-1, -1), 3 * mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm)]),
        PageBreak(),
        Paragraph("Workflow", S["h1"]),
        Paragraph("The planned workflow converts raw scans into clinically interpretable measurements through a reproducible sequence.", S["body"]),
        StepFlow([
            ("Data acquisition", "Collect angiography, CTA, or related vessel images with expert annotations."),
            ("Preprocessing", "Standardize size and intensity; reduce noise; enhance vessels; augment training data."),
            ("Artery segmentation", "Train a deep encoder-decoder network to predict a pixel-level vessel mask."),
            ("Post-processing", "Remove artifacts, retain connected vessels, and derive centerlines and diameters."),
            ("Stenosis analysis", "Compare local vessel diameter with a reference segment to estimate narrowing."),
            ("Evaluation and reporting", "Measure segmentation quality and present overlays, location, and severity."),
        ], box_h=15 * mm, gap=3 * mm),
        Spacer(1, 5 * mm),
        Paragraph("Architecture", S["h1"]),
        Paragraph("The initial architecture is a two-stage system. The first stage performs semantic segmentation using an encoder-decoder network such as U-Net or an attention-enhanced variant. The encoder learns multi-scale image features; skip connections preserve fine vessel boundaries; and the decoder reconstructs a high-resolution binary artery mask.", S["body"]),
        Paragraph("The second stage analyzes the segmented vessel geometry. Centerline extraction and diameter profiling locate abrupt reductions in lumen width. A stenosis estimation module then reports the suspected region and percentage narrowing, while a visualization layer overlays results on the source image.", S["body"]),
        Table([[Paragraph("INPUT", S["center"]), Paragraph("SEGMENTATION", S["center"]), Paragraph("GEOMETRIC ANALYSIS", S["center"]), Paragraph("OUTPUT", S["center"])], [Paragraph("Medical image", S["center"]), Paragraph("Encoder - decoder + skip connections", S["center"]), Paragraph("Centerline + diameter profile", S["center"]), Paragraph("Mask + stenosis report", S["center"])]], colWidths=[39 * mm, 49 * mm, 45 * mm, 37 * mm], style=[("BACKGROUND", (0, 0), (-1, 0), BLUE), ("TEXTCOLOR", (0, 0), (-1, 0), WHITE), ("BACKGROUND", (0, 1), (-1, 1), PALE), ("GRID", (0, 0), (-1, -1), 0.7, LINE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 4 * mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm)]),
        Spacer(1, 5 * mm),
        Paragraph("Architecture details will be refined when the dataset, imaging modality, model variant, and stenosis grading method are finalized.", S["small"]),
    ]
    doc.build(story)
    return path


def daily_work_log():
    path = OUT / "daily_project_work_log.pdf"
    doc = make_doc(path, "Daily Project Work Log")
    story = [
        Spacer(1, 10 * mm),
        Paragraph("Daily Project Work Log", S["subtitle"]),
        Paragraph("Artery Segmentation and Stenosis Detection using Advanced Deep Learning Techniques", S["title"]),
        Paragraph("An ongoing date-wise record of completed work, decisions, results, issues, and planned activities.", S["subtitle"]),
        Table([[Paragraph("DATE", S["center"]), Paragraph("PHASE", S["center"]), Paragraph("STATUS", S["center"])], [Paragraph("08 October 2026", S["center"]), Paragraph("Project definition and documentation", S["center"]), Paragraph("Completed", S["center"])]], colWidths=[55 * mm, 70 * mm, 45 * mm], style=[("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), WHITE), ("BACKGROUND", (0, 1), (-1, 1), PALE), ("GRID", (0, 0), (-1, -1), 0.7, LINE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 4 * mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm)]),
        Spacer(1, 8 * mm),
        Paragraph("Project objective", S["h1"]),
        Paragraph("Build an advanced deep learning pipeline that segments arteries from medical images and analyzes vessel geometry to identify the location and estimated severity of stenosis.", S["body"]),
        Paragraph("Today's work", S["h1"]),
        Paragraph("1. Defined the project title and the intended medical-image-analysis scope.", S["body"]),
        Paragraph("2. Established the core objective: artery segmentation followed by stenosis detection and quantification.", S["body"]),
        Paragraph("3. Prepared the initial end-to-end workflow covering data collection, preprocessing, model training, post-processing, stenosis analysis, evaluation, and reporting.", S["body"]),
        Paragraph("4. Drafted a two-stage architecture consisting of a deep segmentation network and a geometry-based stenosis analysis module.", S["body"]),
        Paragraph("5. Created separate project-documentation and daily-work records so future technical progress can be tracked consistently.", S["body"]),
        PageBreak(),
        Paragraph("Current workflow summary", S["h1"]),
        StepFlow([
            ("Medical images", "Provide arterial scans and matching reference annotations."),
            ("Image preparation", "Normalize, enhance, resize, and augment the data."),
            ("Deep segmentation", "Generate a pixel-level artery mask."),
            ("Stenosis detection", "Measure vessel narrowing from mask-derived geometry."),
            ("Clinical-style output", "Display overlays, suspected location, and severity estimate."),
        ], box_h=14 * mm, gap=3 * mm),
        Spacer(1, 5 * mm),
        Paragraph("Initial architecture note", S["h1"]),
        Paragraph("The system will use an encoder-decoder segmentation network, initially represented by U-Net or an attention-based variant. Skip connections will preserve vessel boundaries. The cleaned mask will support centerline and diameter analysis, after which local lumen diameter will be compared with a reference segment to estimate stenosis. Model choice and grading thresholds remain provisional until the dataset and clinical definition are confirmed.", S["body"]),
        Paragraph("Decisions recorded", S["h1"]),
        Table([[Paragraph("Item", S["center"]), Paragraph("Decision", S["center"])], [Paragraph("Documentation structure", S["body"]), Paragraph("Maintain one technical document and one date-wise work log.", S["body"])], [Paragraph("System structure", S["body"]), Paragraph("Use a segmentation stage followed by stenosis measurement and visualization.", S["body"])], [Paragraph("Implementation detail", S["body"]), Paragraph("Keep model, modality, dataset, and thresholds open until evidence is available.", S["body"])]], colWidths=[50 * mm, 120 * mm], style=[("BACKGROUND", (0, 0), (-1, 0), BLUE), ("TEXTCOLOR", (0, 0), (-1, 0), WHITE), ("GRID", (0, 0), (-1, -1), 0.6, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm), ("TOPPADDING", (0, 0), (-1, -1), 3 * mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm)]),
        Spacer(1, 6 * mm),
        Paragraph("Next planned work", S["h1"]),
        Paragraph("Identify the imaging modality and dataset; review annotation formats; define data splits; select the baseline model; and establish Dice, IoU, sensitivity, specificity, and stenosis-measurement metrics.", S["body"]),
        Paragraph("This entry records the initial project definition. Future entries will be appended chronologically as work is reported.", S["small"]),
    ]
    doc.build(story)
    return path


if __name__ == "__main__":
    for generated in (project_documentation(), daily_work_log()):
        print(generated)
