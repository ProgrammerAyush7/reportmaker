from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    Spacer,
    Paragraph,
    PageBreak,
    KeepTogether
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def generate_pdf_report(report_json, patient_info, template_image, output_file="report.pdf"):

    # =========================================================
    # PAGE + REPORT AREA SETTINGS
    # =========================================================

    PAGE_SIZE = A4

    REPORT_TOP_MARGIN = 200
    REPORT_BOTTOM_MARGIN = 200

    PAGE_LEFT_MARGIN = 40
    PAGE_RIGHT_MARGIN = 40

    MAX_TESTS_PER_PAGE = 20


    # =========================================================
    # HEADER LAYOUT SETTINGS
    # =========================================================

    HEADER_TOP_OFFSET = 165
    HEADER_LINE_SPACING = 20

    HEADER_LEFT_X = 40
    HEADER_RIGHT_X_1 = 380
    HEADER_RIGHT_X_2 = 470

    HEADER_FONT_NAME = "Arial-Bold"
    HEADER_FONT_SIZE = 10


    # =========================================================
    # CATEGORY TITLE SETTINGS
    # =========================================================

    CATEGORY_FONT_NAME = "Arial-Bold"
    CATEGORY_FONT_SIZE = 12
    CATEGORY_ALIGNMENT = 1

    CATEGORY_SPACE_AFTER = 15


    # =========================================================
    # TABLE COLUMN SETTINGS
    # =========================================================

    COLUMN_TEST_WIDTH = 200
    COLUMN_READING_WIDTH = 80
    COLUMN_UNIT_WIDTH = 70
    COLUMN_RANGE_WIDTH = 170

    COLUMN_WIDTHS = [
        COLUMN_TEST_WIDTH,
        COLUMN_READING_WIDTH,
        COLUMN_UNIT_WIDTH,
        COLUMN_RANGE_WIDTH
    ]


    # =========================================================
    # TABLE FONT SETTINGS
    # =========================================================

    COLUMN_HEADER_FONT = "Arial-Bold"
    COLUMN_HEADER_FONT_SIZE = 10

    DATA_FONT = "Arial"
    DATA_FONT_SIZE = 10


    # =========================================================
    # TABLE SPACING + PADDING SETTINGS
    # =========================================================

    TABLE_HEADER_TOP_PADDING = 6
    TABLE_HEADER_BOTTOM_PADDING = 6

    TABLE_ROW_TOP_PADDING = 3
    TABLE_ROW_BOTTOM_PADDING = 3

    TABLE_SPACE_AFTER = 8
    CATEGORY_END_LINE_SPACE = 12

    CONTINUATION_ROW_TOP_PADDING = 1
    CONTINUATION_ROW_BOTTOM_PADDING = 1

    SUBTEST_INDENT_HTML = "&nbsp;&nbsp;&nbsp;&nbsp;"


    # =========================================================
    # FONT REGISTRATION
    # =========================================================

    pdfmetrics.registerFont(TTFont("Arial", "arial.ttf"))
    pdfmetrics.registerFont(TTFont("Arial-Bold", "arialbd.ttf"))

    page_width, page_height = PAGE_SIZE


    # =========================================================
    # DOCUMENT
    # =========================================================

    doc = SimpleDocTemplate(
        output_file,
        pagesize=PAGE_SIZE,
        leftMargin=PAGE_LEFT_MARGIN,
        rightMargin=PAGE_RIGHT_MARGIN,
        topMargin=REPORT_TOP_MARGIN,
        bottomMargin=REPORT_BOTTOM_MARGIN
    )


    # =========================================================
    # STYLES
    # =========================================================

    category_style = ParagraphStyle(
        "Category",
        fontName=CATEGORY_FONT_NAME,
        fontSize=CATEGORY_FONT_SIZE,
        alignment=CATEGORY_ALIGNMENT
    )

    column_style = ParagraphStyle(
        "Column",
        fontName=COLUMN_HEADER_FONT,
        fontSize=COLUMN_HEADER_FONT_SIZE
    )

    data_style = ParagraphStyle(
        "Data",
        fontName=DATA_FONT,
        fontSize=DATA_FONT_SIZE
    )


    # =========================================================
    # HELPERS
    # =========================================================

    def clean(value):
        if value in [None, "None"]:
            return ""
        return str(value)


    def draw_page(canvas, doc):

        canvas.saveState()

        canvas.drawImage(
            template_image,
            0,
            0,
            width=page_width,
            height=page_height,
            preserveAspectRatio=False,
            mask='auto'
        )

        line1_y = page_height - HEADER_TOP_OFFSET
        line2_y = line1_y - HEADER_LINE_SPACING

        canvas.setFont(HEADER_FONT_NAME, HEADER_FONT_SIZE)

        canvas.drawString(
            HEADER_LEFT_X,
            line1_y,
            f"NAME OF THE PATIENT: {patient_info.get('name','')}".upper()
        )

        canvas.drawString(
            HEADER_RIGHT_X_1,
            line1_y,
            f"AGE: {patient_info.get('age','')}".upper()
        )

        canvas.drawString(
            HEADER_RIGHT_X_2,
            line1_y,
            f"SEX: {patient_info.get('sex','')}".upper()
        )

        canvas.drawString(
            HEADER_LEFT_X,
            line2_y,
            f"REFERRED BY DOCTOR: {patient_info.get('referred_by','')}".upper()
        )

        canvas.drawString(
            HEADER_RIGHT_X_1,
            line2_y,
            f"DATE: {patient_info.get('date','')}".upper()
        )

        canvas.drawString(
            HEADER_RIGHT_X_2,
            line2_y,
            f"ID: {patient_info.get('id','')}"
        )

        canvas.restoreState()


    # =========================================================
    # NORMALIZE TEST BLOCKS
    # =========================================================

    def build_test_blocks(tests):

        def split_cell(value):
            value = clean(value)
            return value.split("$") if value else [""]

        def build_rows(name, reading, unit, normal_range, indent=False):

            name_parts = split_cell(name)
            reading_parts = split_cell(reading)
            unit_parts = split_cell(unit)
            range_parts = split_cell(normal_range)

            max_lines = max(
                len(name_parts),
                len(reading_parts),
                len(unit_parts),
                len(range_parts)
            )

            rows = []

            for i in range(max_lines):

                n = name_parts[i] if i < len(name_parts) else ""
                r = reading_parts[i] if i < len(reading_parts) else ""
                u = unit_parts[i] if i < len(unit_parts) else ""
                rg = range_parts[i] if i < len(range_parts) else ""

                if indent and n:
                    n = SUBTEST_INDENT_HTML + n

                rows.append({
                    "cells": [
                        Paragraph(n, data_style) if n else "",
                        Paragraph(r, data_style) if r else "",
                        Paragraph(u, data_style) if u else "",
                        Paragraph(rg, data_style) if rg else "",
                    ],
                    "continuation": i > 0
                })

            return rows, max_lines

        blocks = []
        i = 0
        n = len(tests)

        while i < n:

            test = tests[i]
            name = test["test"]

            # -----------------------------------------------------
            # SINGLE TEST
            # -----------------------------------------------------
            if " - " not in name:

                rows, size = build_rows(
                    name,
                    test["reading"],
                    test["unit"],
                    test["normal_range"]
                )

                blocks.append({
                    "size": size,
                    "rows": rows
                })

                i += 1
                continue

            # -----------------------------------------------------
            # GROUPED TEST
            # -----------------------------------------------------
            main, _ = name.split(" - ", 1)

            rows = [
                [Paragraph(main, data_style), "", "", ""]
            ]

            size = 1

            while i < n and " - " in tests[i]["test"]:

                current_main, sub = tests[i]["test"].split(" - ", 1)

                if current_main != main:
                    break

                sub_rows, sub_size = build_rows(
                    sub,
                    tests[i]["reading"],
                    tests[i]["unit"],
                    tests[i]["normal_range"],
                    indent=True
                )

                rows.extend(sub_rows)
                size += sub_size

                i += 1

            blocks.append({
                "size": size,
                "rows": rows
            })

        return blocks
    # =========================================================
    # PAGINATION
    # =========================================================

    def extract_urine_section(report_json):
        normal_report = []
        urine_section = None

        for category_block in report_json["report"]:
            category_name = clean(category_block.get("category", "")).strip().lower()

            if category_name == "urine":
                urine_section = category_block
            else:
                normal_report.append(category_block)

        return {"report": normal_report}, urine_section

    def paginate(report_json):

        pages = []
        current_page = []
        current_count = 0

        for category_block in report_json["report"]:

            category = category_block["category"]
            blocks = build_test_blocks(category_block["tests"])

            category_cost = 3
            first_block_size = blocks[0]["size"] if blocks else 0

            required_space = category_cost + first_block_size

            if current_count + required_space > MAX_TESTS_PER_PAGE:
                if current_page:
                    pages.append(current_page)
                current_page = []
                current_count = 0

            current_page.append({
                "type": "category",
                "name": category,
                "blocks": []
            })

            current_count += category_cost

            for block in blocks:

                if current_count + block["size"] > MAX_TESTS_PER_PAGE:
                    pages.append(current_page)

                    current_page = [{
                        "type": "category",
                        "name": category,
                        "blocks": []
                    }]

                    current_count = category_cost

                current_page[-1]["blocks"].append(block)
                current_count += block["size"]

        if current_page:
            pages.append(current_page)

        return pages


    # =========================================================
    # RENDERING
    # =========================================================

    def make_table(rows):

        table_rows = []
        continuation_rows = []

        for idx, row in enumerate(rows):

            if isinstance(row, dict):
                table_rows.append(row["cells"])

                if row.get("continuation"):
                    continuation_rows.append(idx)

            else:
                table_rows.append(row)

        table = Table(
            table_rows,
            colWidths=COLUMN_WIDTHS,
            repeatRows=1
        )

        style = [
            ("LINEABOVE", (0, 0), (-1, 0), 1, colors.black),
            ("LINEBELOW", (0, 0), (-1, 0), 1, colors.black),

            ("TOPPADDING", (0, 0), (-1, 0), TABLE_HEADER_TOP_PADDING),
            ("BOTTOMPADDING", (0, 0), (-1, 0), TABLE_HEADER_BOTTOM_PADDING),

            ("TOPPADDING", (0, 1), (-1, -1), TABLE_ROW_TOP_PADDING),
            ("BOTTOMPADDING", (0, 1), (-1, -1), TABLE_ROW_BOTTOM_PADDING),
        ]

        for row_index in continuation_rows:
            style.append(
                ("TOPPADDING", (0, row_index), (-1, row_index), CONTINUATION_ROW_TOP_PADDING)
            )
            style.append(
                ("BOTTOMPADDING", (0, row_index), (-1, row_index), CONTINUATION_ROW_BOTTOM_PADDING)
            )

        table.setStyle(style)

        return table


    def end_line():
        line = Table(
            [[""]],
            colWidths=[sum(COLUMN_WIDTHS)],
            rowHeights=[0]
        )

        line.setStyle([
            ("LINEBELOW", (0, 0), (-1, 0), 1, colors.black),
            ("TOPPADDING", (0, 0), (-1, 0), 0),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 0),
            ("LEFTPADDING", (0, 0), (-1, 0), 0),
            ("RIGHTPADDING", (0, 0), (-1, 0), 0),
        ])

        return line
    
    def render_urine_section(urine_section):

        if not urine_section or not urine_section.get("tests"):
            return []

        urine_test = urine_section["tests"][0]
        values = [v.strip() for v in clean(urine_test.get("reading")).split(",")]

        # keep only first 18 values
        values = values[:18]

        # pad missing values
        while len(values) < 18:
            values.append("")

        urine_values = {}
        all_tests = [
            "Nature",
            "Appearance",
            "Quantity",
            "Colour",
            "Specific Gravity",
            "Albumin",
            "Sugar",
            "Ketones",
            "Bile salts",
            "Bile Pigment",
            "Epithelial cell",
            "RBCs",
            "Pus cell",
            "Amorphous",
            "Casts",
            "Crystals",
            "Bacteria",
            "Sperms"
        ]

        for i, name in enumerate(all_tests):
            urine_values[name] = values[i] if i < len(values) else ""

        section_style = ParagraphStyle(
            "UrineSection",
            fontName=CATEGORY_FONT_NAME,
            fontSize=CATEGORY_FONT_SIZE,
            alignment=1
        )

        urine_style = ParagraphStyle(
            "UrineData",
            fontName=DATA_FONT,
            fontSize=DATA_FONT_SIZE
        )

        def make_urine_row(left_label, right_label=None):

            def p(text):
                text = clean(text)
                return Paragraph(text if text else "&nbsp;", urine_style)

            left_value = urine_values.get(left_label, "")
            right_value = urine_values.get(right_label, "") if right_label else ""

            return [
                p(left_label),
                p(":"),
                p(left_value),

                p(right_label) if right_label else p(""),
                p(":") if right_label else p(""),
                p(right_value) if right_label else p(""),
            ]

        def make_section(title, rows):

            section_elements = []

            section_elements.append(end_line())
            section_elements.append(Spacer(1, 12))

            section_elements.append(
                Paragraph(title, section_style)
            )

            section_elements.append(Spacer(1, 12))
            section_elements.append(end_line())
            section_elements.append(Spacer(1, 16))

            table = Table(
                rows,
                colWidths=[100, 10, 165, 100, 10, 115]
            )

            table.setStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (1, 1), 2),
                ("BOTTOMPADDING", (0, 0), (1, 1), 2),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ])

            section_elements.append(table)
            section_elements.append(Spacer(1, 16))

            return section_elements

        elements = []

        # ---------------------------------------------------------
        # REPORT TITLE
        # ---------------------------------------------------------

        elements.append(
            Paragraph("REPORT ON URINE ANALYSIS", category_style)
        )

        elements.append(Spacer(1, CATEGORY_SPACE_AFTER))

        # ---------------------------------------------------------
        # PHYSICAL EXAMINATION
        # ---------------------------------------------------------

        physical_rows = [
            make_urine_row("Nature", "Appearance"),
            make_urine_row("Quantity", "Colour"),
            make_urine_row("Specific Gravity"),
        ]

        elements.extend(
            make_section("PHYSICAL EXAMINATION", physical_rows)
        )

        # ---------------------------------------------------------
        # CHEMICAL EXAMINATION
        # ---------------------------------------------------------

        chemical_rows = [
            make_urine_row("Albumin", "Sugar"),
            make_urine_row("Ketones", "Bile salts"),
            make_urine_row("Bile Pigment"),
        ]

        elements.extend(
            make_section("CHEMICAL EXAMINATION", chemical_rows)
        )

        # ---------------------------------------------------------
        # MICROSCOPY
        # ---------------------------------------------------------

        microscopy_rows = [
            make_urine_row("Epithelial cell", "RBCs"),
            make_urine_row("Pus cell", "Amorphous"),
            make_urine_row("Casts", "Crystals"),
            make_urine_row("Bacteria", "Sperms"),
        ]

        elements.extend(
            make_section("MICROSCOPY", microscopy_rows)
        )

        elements.append(end_line())

        return elements


    normal_report, urine_section = extract_urine_section(report_json)
    pages = paginate(normal_report)

    elements = []

    for page_index, page in enumerate(pages):

        for category in page:

            elements.append(
                Paragraph(
                    f"REPORT ON {category['name'].upper()}",
                    category_style
                )
            )

            elements.append(Spacer(1, CATEGORY_SPACE_AFTER))

            table_rows = [[
                Paragraph("NAME OF TEST", column_style),
                Paragraph("READING", column_style),
                Paragraph("UNIT", column_style),
                Paragraph("NORMAL RANGE", column_style)
            ]]

            for block in category["blocks"]:
                table_rows.extend(block["rows"])

            elements.append(make_table(table_rows))
            elements.append(Spacer(1, TABLE_SPACE_AFTER))
            elements.append(end_line())
            elements.append(Spacer(1, CATEGORY_END_LINE_SPACE))

        if page_index < len(pages) - 1:
            elements.append(PageBreak())


    # ---------------------------------------------------------
    # URINE PAGE (ALWAYS LAST)
    # ---------------------------------------------------------

    if urine_section:

        urine_elements = render_urine_section(urine_section)

        if elements:
            elements.append(PageBreak())

        elements.append(
            KeepTogether(urine_elements)
        )
    # =========================================================
    # BUILD
    # =========================================================

    doc.build(
        elements,
        onFirstPage=draw_page,
        onLaterPages=draw_page
    )