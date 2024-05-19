from io import BytesIO
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.shared import Mm


def build_report(
    filtered_reports_dict: dict,
    start_date: str,
    end_date: str,
    uniq: int,
    total_points: int
    ):

    document = Document()

    style = document.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(12)
    
    section = document.sections[0]
    section.right_margin = Mm(10)
    section.top_margin = Mm(15)
    section.bottom_margin = Mm(10)
    section.header_distance = Mm(10)
    section.footer_distance = Mm(10)
    
    head = document.add_heading('Отчет по оперативной обстановке\n {} - {}\n Уникальность информации - {}%'.format(start_date, end_date, uniq))
    head.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

    for key in filtered_reports_dict:
        
        if len(filtered_reports_dict[key]) != 0:
            par = document.add_paragraph().add_run(key.capitalize())
            par.font.size = Pt(14)
            par.bold = True

            for point in range(len(filtered_reports_dict[key])):
                par0 = document.add_paragraph(str(point+1) + ') ')
                par0.add_run(filtered_reports_dict[key][point].strip())
                par0.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
                fmt0 = par0.paragraph_format
                fmt0.first_line_indent = Mm(15)

    target_stream = BytesIO()
    document.save(target_stream)
    
    return target_stream, total_points
