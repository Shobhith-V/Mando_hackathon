import fitz  # PyMuPDF
import docx
import pptx
import pandas as pd
import json

def parse_pdf(file):
    try:
        # Ensure file is read as byte stream
        doc = fitz.open(stream=file.read(), filetype="pdf")
        return "\n".join([page.get_text() for page in doc])
    except Exception as e:
        return f"Error parsing PDF: {e}"

def parse_docx(file):
    try:
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        return f"Error parsing DOCX: {e}"

def parse_pptx(file):
    try:
        prs = pptx.Presentation(file)
        text = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text.append(shape.text)
        return "\n".join(text)
    except Exception as e:
        return f"Error parsing PPTX: {e}"

def parse_csv_or_excel(file, filetype):
    try:
        if filetype == "csv":
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        return df.to_string(index=False)
    except Exception as e:
        return f"Error parsing CSV/Excel: {e}"

def parse_txt(file):
    try:
        return file.read().decode("utf-8")
    except Exception as e:
        return f"Error parsing TXT: {e}"

def parse_json(file):
    try:
        return file.read().decode("utf-8")  # You can later json.loads this
    except Exception as e:
        return f"Error parsing JSON: {e}"

def parse_file(file, filetype):
    try:
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
            return "Unsupported file type"
    except Exception as e:
        return f"Error parsing file: {e}"
