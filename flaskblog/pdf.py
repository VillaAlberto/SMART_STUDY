from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from models import Subject

def download(subject_id):
    subject = Subject.get_subject_or_error(subject_id)
    lec = subject.lecture
    document = []
    document.append(Image("flaskblog/static/assets/img/logo.png", 2.2 * inch, 2.2 * inch))
    for lecture in lec:
        Subject_pdf = open("flaskblog/Lecture.txt", "w")
        add_txt = lecture.content
        Subject_pdf.write(add_txt.encode("utf-8"))
        Subject_pdf.close()

        def addTitle(doc):
            doc.append(Spacer(1, 20))
            doc.append(Paragraph(lecture.lecture_name, ParagraphStyle(name='Name',
                                                                      fontFamily='Helvetica',
                                                                      fontsize=36,
                                                                      alignment=TA_CENTER)))

            doc.append(Spacer(1, 50))
            return doc

        def addParagraph(doc):
            with open("flaskblog/Lecture.txt") as txt:
                for line in txt.read().split('\n'):
                    doc.append(Paragraph(line))
                    doc.append(Spacer(1, 12))
            return doc

        document = addTitle(document)
        document = addParagraph(document)

    SimpleDocTemplate('PDF-SMART-STUDY/{}.pdf'.format(subject.subject_name), pagesize=letter,
                      rightMargin=12, leftMargin=12,
                      topMargin=12, bottomMargin=6).build(document)