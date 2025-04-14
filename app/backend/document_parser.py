import fitz  # PyMuPDF
import docx
import pptx
import pandas as pd

def parse_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "\n".join([page.get_text() for page in doc])

def parse_docx(file):
    doc = docx.Document(file)
    return "\n".join([p.text for p in doc.paragraphs])

def parse_pptx(file):
    prs = pptx.Presentation(file)
    text = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text.append(shape.text)
    return "\n".join(text)

def parse_csv_or_excel(file, filetype):
    if filetype == "csv":
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)
    return df.to_string(index=False)

def parse_txt(file):
    return file.read().decode("utf-8")

def parse_json(file):
    return file.read().decode("utf-8")  # You can later json.loads this

def parse_file(file, filetype):
    if filetype == "pdf":
        return parse_pdf(file)
    elif filetype == "docx":
        return parse_docx(file)
    elif filetype == "pptx":
        return parse_pptx(file)
    elif filetype in ["csv", "xlsx"]:
        return parse_csv_or_excel(file, filetype)
    elif filetype == "txt":
        return parse_txt(file)
    elif filetype == "json":
        return parse_json(file)
    else:
        return ""
