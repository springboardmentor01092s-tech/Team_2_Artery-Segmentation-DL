"""Shared layout for printable research summaries."""
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph, SimpleDocTemplate


class ResearchPDF:
    def __init__(self, title):
        self.stream = BytesIO()
        self.document = SimpleDocTemplate(
            self.stream, pagesize=A4, title=f'CoroVision AI | {title}',
            leftMargin=44, rightMargin=44, topMargin=92, bottomMargin=45,
        )
        self.story = []
        self.body = ParagraphStyle('Report body', fontName='Helvetica', fontSize=10,
            leading=15, spaceAfter=6, textColor=colors.HexColor('#273444'))
        self.heading = ParagraphStyle('Report heading', parent=self.body, fontName='Helvetica-Bold',
            fontSize=13, leading=18, spaceBefore=12, spaceAfter=5, keepWithNext=True)
        self.fact = ParagraphStyle('Report field', parent=self.body, spaceAfter=3)
        self.title = ParagraphStyle('Report title', parent=self.heading, fontSize=24,
            leading=29, spaceBefore=0, spaceAfter=12)
        self.story.append(Paragraph(escape(title), self.title))

    def paragraph(self, text):
        self.story.append(Paragraph(escape(str(text)).replace('\n', '<br/>'), self.body))

    def section(self, title):
        self.story.append(Paragraph(escape(title), self.heading))

    def field(self, label, value):
        value = 'Unavailable' if value is None or value == '' else value
        self.story.append(Paragraph(f'<b>{escape(label)}</b>  {escape(str(value))}', self.fact))

    def build(self):
        frontend = Path(__file__).resolve().parents[2] / 'frontend'
        logo_path = next((path for path in (
            frontend / 'dist/corovision-heart-mark.png',
            frontend / 'public/corovision-heart-mark.png',
        ) if path.is_file()), None)
        logo = None
        if logo_path:
            from PIL import Image
            with Image.open(logo_path) as original:
                original.thumbnail((144, 144))
                logo = ImageReader(original.copy())

        def furniture(canvas, doc):
            width, height = A4
            if logo is not None:
                canvas.drawImage(logo, 44, height - 65, 30, 30, mask='auto')
            canvas.setFillColor(colors.HexColor('#1e2e40'))
            canvas.setFont('Helvetica-Bold', 13)
            canvas.drawString(82 if logo else 44, height - 54, 'CoroVision AI')
            canvas.setStrokeColor(colors.HexColor('#d7e0ea'))
            canvas.line(44, height - 75, width - 44, height - 75)
            canvas.line(44, 34, width - 44, 34)
            canvas.setFont('Helvetica', 8)
            canvas.drawString(44, 21, 'Research use only')
            canvas.drawRightString(width - 44, 21, f'Page {doc.page}')

        self.document.build(self.story, onFirstPage=furniture, onLaterPages=furniture)
        return self.stream.getvalue()
