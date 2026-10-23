import os
import sys

class PDFDocument:
    def __init__(self, filename, title="Document", page_width=595.28, page_height=841.89):
        self.filename = filename
        self.title = title
        self.w = page_width
        self.h = page_height
        self.margin_x = 48.0
        self.margin_top = 48.0
        self.margin_bottom = 48.0
        self.usable_width = self.w - (2 * self.margin_x)
        
        self.pages = []
        self.current_stream = []
        self.y = self.h - self.margin_top
        self.page_number = 0
        self.new_page()

    def new_page(self):
        if self.page_number > 0:
            self.pages.append("".join(self.current_stream))
            self.current_stream = []
        self.page_number += 1
        self.y = self.h - self.margin_top

    def check_space(self, height_needed):
        if self.y - height_needed < self.margin_bottom:
            self.new_page()

    def raw(self, cmd):
        self.current_stream.append(cmd + "\n")

    def draw_line(self, x1, y1, x2, y2, stroke=(0.0, 0.0, 0.0), line_width=0.75):
        cmd = f"q {line_width:.2f} w {stroke[0]:.3f} {stroke[1]:.3f} {stroke[2]:.3f} RG {x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S Q"
        self.raw(cmd)

    def draw_text(self, x, y, text, font="F1", size=10, color=(0.0, 0.0, 0.0)):
        esc = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        cmd = f"q BT /{font} {size:.2f} Tf {color[0]:.3f} {color[1]:.3f} {color[2]:.3f} rg {x:.2f} {y:.2f} Td ({esc}) Tj ET Q"
        self.raw(cmd)

    def estimate_text_width(self, text, font="F1", size=10):
        factor = 0.52
        if "Bold" in font or font in ("F2", "F5"):
            factor = 0.57
        elif font in ("F4", "F5"):
            factor = 0.60
        return len(text) * size * factor

    def wrap_text(self, text, max_width, font="F1", size=10):
        words = text.split(" ")
        lines = []
        curr_line = []
        for word in words:
            test_line = " ".join(curr_line + [word]) if curr_line else word
            w = self.estimate_text_width(test_line, font, size)
            if w <= max_width:
                curr_line.append(word)
            else:
                if curr_line:
                    lines.append(" ".join(curr_line))
                    curr_line = [word]
                else:
                    lines.append(word)
                    curr_line = []
        if curr_line:
            lines.append(" ".join(curr_line))
        return lines

    def add_main_title(self, title, doc_type=""):
        self.check_space(60)
        if doc_type:
            self.draw_text(self.margin_x, self.y - 10, doc_type.upper(), font="F2", size=9.0, color=(0.0, 0.0, 0.0))
            self.y -= 14

        # Wrap title
        title_lines = self.wrap_text(title, self.usable_width, font="F2", size=16.0)
        for line in title_lines:
            self.draw_text(self.margin_x, self.y - 16, line, font="F2", size=16.0, color=(0.0, 0.0, 0.0))
            self.y -= 20
        
        self.y -= 4
        # Solid black divider line
        self.draw_line(self.margin_x, self.y, self.margin_x + self.usable_width, self.y, stroke=(0.0, 0.0, 0.0), line_width=1.5)
        self.y -= 16

    def add_section_header(self, title):
        self.check_space(34)
        self.y -= 8
        self.draw_text(self.margin_x, self.y - 12, title, font="F2", size=12.0, color=(0.0, 0.0, 0.0))
        self.y -= 16
        self.draw_line(self.margin_x, self.y, self.margin_x + self.usable_width, self.y, stroke=(0.0, 0.0, 0.0), line_width=0.75)
        self.y -= 12

    def add_subsection_header(self, title):
        self.check_space(24)
        self.y -= 4
        self.draw_text(self.margin_x, self.y - 10, title, font="F2", size=10.0, color=(0.0, 0.0, 0.0))
        self.y -= 15

    def add_paragraph(self, text, size=9.5, line_spacing=13.5):
        lines = self.wrap_text(text, self.usable_width, font="F1", size=size)
        for line in lines:
            self.check_space(line_spacing + 2)
            self.draw_text(self.margin_x, self.y - size, line, font="F1", size=size, color=(0.0, 0.0, 0.0))
            self.y -= line_spacing
        self.y -= 4

    def add_bullet(self, bold_prefix, text, size=9.5, line_spacing=13.0):
        prefix_str = f"-  {bold_prefix} " if bold_prefix else "-  "
        full_text = prefix_str + text
        lines = self.wrap_text(full_text, self.usable_width - 10, font="F1", size=size)
        for i, line in enumerate(lines):
            self.check_space(line_spacing + 2)
            if i == 0 and bold_prefix:
                p_w = self.estimate_text_width(f"-  {bold_prefix} ", "F2", size)
                self.draw_text(self.margin_x + 6, self.y - size, f"-  {bold_prefix} ", font="F2", size=size, color=(0.0, 0.0, 0.0))
                rest = line[len(f"-  {bold_prefix} "):] if line.startswith(f"-  {bold_prefix} ") else ""
                if rest:
                    self.draw_text(self.margin_x + 6 + p_w, self.y - size, rest, font="F1", size=size, color=(0.0, 0.0, 0.0))
            else:
                indent = 16 if i > 0 else 6
                self.draw_text(self.margin_x + indent, self.y - size, line, font="F1", size=size, color=(0.0, 0.0, 0.0))
            self.y -= line_spacing
        self.y -= 2

    def add_table_row(self, cols, widths=None, is_header=False, size=8.0, row_height=14.0):
        self.check_space(row_height + 2)
        if widths is None:
            w_each = self.usable_width / len(cols)
            widths = [w_each] * len(cols)
        
        y_box = self.y - row_height
        f = "F2" if is_header else "F1"
        
        line_w = 1.0 if is_header else 0.5
        self.draw_line(self.margin_x, y_box, self.margin_x + self.usable_width, y_box, stroke=(0.0, 0.0, 0.0), line_width=line_w)
        if is_header:
            self.draw_line(self.margin_x, self.y, self.margin_x + self.usable_width, self.y, stroke=(0.0, 0.0, 0.0), line_width=1.0)
            
        cur_x = self.margin_x
        for i, text in enumerate(cols):
            w = widths[i]
            self.draw_text(cur_x + 4, y_box + 4, str(text), font=f, size=size, color=(0.0, 0.0, 0.0))
            cur_x += w
        self.y = y_box

    def add_code_block(self, lines, size=7.5, line_spacing=10.0):
        for line in lines:
            self.check_space(line_spacing + 2)
            self.draw_text(self.margin_x + 6, self.y - size, line, font="F4", size=size, color=(0.0, 0.0, 0.0))
            self.y -= line_spacing
        self.y -= 4

    def save(self):
        if self.current_stream:
            self.pages.append("".join(self.current_stream))
            self.current_stream = []

        total_pages = len(self.pages)
        final_pages = []
        for i, page_content in enumerate(self.pages):
            pnum = i + 1
            decorations = []
            
            # Simple header on page 2+
            if pnum > 1:
                decorations.append(f"q BT /F1 8.0 Tf 0.0 0.0 0.0 rg {self.margin_x:.2f} {self.h - 28:.2f} Td ({self.title}) Tj ET Q\n")
                decorations.append(f"q 0.5 w 0.0 0.0 0.0 RG {self.margin_x:.2f} {self.h - 32:.2f} m {self.margin_x + self.usable_width:.2f} {self.h - 32:.2f} l S Q\n")

            # Simple black-and-white footer
            footer_y = 28.0
            decorations.append(f"q 0.5 w 0.0 0.0 0.0 RG {self.margin_x:.2f} {footer_y + 10:.2f} m {self.margin_x + self.usable_width:.2f} {footer_y + 10:.2f} l S Q\n")
            decorations.append(f"q BT /F1 8.0 Tf 0.0 0.0 0.0 rg {self.margin_x:.2f} {footer_y:.2f} Td ({self.title}) Tj ET Q\n")
            page_str = f"Page {pnum} of {total_pages}"
            pw = self.estimate_text_width(page_str, "F1", 8.0)
            decorations.append(f"q BT /F1 8.0 Tf 0.0 0.0 0.0 rg {self.margin_x + self.usable_width - pw:.2f} {footer_y:.2f} Td ({page_str}) Tj ET Q\n")
            
            final_pages.append("".join(decorations) + page_content)

        objs = {}
        page_obj_ids = [8 + j * 2 for j in range(total_pages)]
        stream_obj_ids = [9 + j * 2 for j in range(total_pages)]
        
        objs[1] = f"<< /Type /Catalog /Pages 2 0 R >>"
        kids_str = " ".join([f"{pid} 0 R" for pid in page_obj_ids])
        objs[2] = f"<< /Type /Pages /Kids [{kids_str}] /Count {total_pages} >>"
        objs[3] = f"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
        objs[4] = f"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>"
        objs[5] = f"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique >>"
        objs[6] = f"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>"
        objs[7] = f"<< /Type /Font /Subtype /Type1 /BaseFont /Courier-Bold >>"

        for j in range(total_pages):
            pid = page_obj_ids[j]
            sid = stream_obj_ids[j]
            objs[pid] = f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {self.w:.2f} {self.h:.2f}] /Contents {sid} 0 R /Resources << /Font << /F1 3 0 R /F2 4 0 R /F3 5 0 R /F4 6 0 R /F5 7 0 R >> >> >>"
            sdata = final_pages[j].encode("latin1", errors="replace")
            objs[sid] = f"<< /Length {len(sdata)} >>\nstream\n{final_pages[j]}endstream"

        total_objs = max(objs.keys())
        offsets = {}
        out = [b"%PDF-1.4\n"]

        for oid in range(1, total_objs + 1):
            offsets[oid] = sum(len(x) for x in out)
            val = objs[oid]
            out.append(f"{oid} 0 obj\n{val}\nendobj\n".encode("latin1", errors="replace"))

        startxref = sum(len(x) for x in out)
        out.append(f"xref\n0 {total_objs + 1}\n0000000000 65535 f \n".encode("latin1"))
        for oid in range(1, total_objs + 1):
            out.append(f"{offsets[oid]:010d} 00000 n \n".encode("latin1"))

        out.append(f"trailer\n<< /Size {total_objs + 1} /Root 1 0 R >>\nstartxref\n{startxref}\n%%EOF\n".encode("latin1"))

        with open(self.filename, "wb") as f:
            f.write(b"".join(out))
        print(f"Successfully generated {self.filename} ({total_pages} pages)")
