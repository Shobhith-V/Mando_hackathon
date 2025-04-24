import fitz  # PyMuPDF
import io
from PIL import Image
from backend.ocr_engine import ocr_image_bytes  
from pptx import Presentation
from io import BytesIO
import os

def parse_pdf(file):
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        full_text = []
        
        for page_num, page in enumerate(doc):
            # 1. Extract visible text
            page_text = page.get_text()
            if page_text:
                full_text.append(f"Page {page_num+1} Text:\n{page_text}")
            
            # 2. Extract and OCR images
            img_list = page.get_images(full=True)
            
            for img_index, img in enumerate(img_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                
                # Use centralized OCR function
                ocr_result = ocr_image_bytes(base_image["image"])
                
                full_text.append(
                    f"\nPage {page_num+1} Image {img_index+1} OCR:\n{ocr_result}"
                )
        
        return "\n".join(full_text)
    except Exception as e:
        return f"PDF Error: {str(e)}"
    

def parse_txt(file):
    try:
        return file.read().decode("utf-8")
    except Exception as e:
        return f"Error parsing TXT: {e}"

import json

def parse_json(file):
    try:
        content = file.read().decode("utf-8")
        data = json.loads(content)
        return data  # Return dictionary or list
    except Exception as e:
        return f"JSON Error: {str(e)}"

    
import pandas as pd

def parse_csv(file):
    try:
        df = pd.read_csv(file)
        return df  # Return DataFrame for downstream use
    except Exception as e:
        return f"CSV Error: {str(e)}"

def parse_xlsx(file):
    try:
        df = pd.read_excel(file)
        return df
    except Exception as e:
        return f"XLSX Error: {str(e)}"


def parse_pptx(file, image_output_dir="pptx_images"):
    try:
        prs = Presentation(file)
        text_runs = []
        images = []

        # Create output directory for images if it doesn't exist
        if not os.path.exists(image_output_dir):
            os.makedirs(image_output_dir)

        for slide_idx, slide in enumerate(prs.slides):
            for shape_idx, shape in enumerate(slide.shapes):
                if hasattr(shape, "text"):
                    text_runs.append(shape.text)
                if shape.shape_type == 13:  # PICTURE
                    image = shape.image
                    image_bytes = image.blob
                    image_format = image.ext  # e.g., 'jpeg', 'png'
                    image_filename = f"slide{slide_idx+1}_img{shape_idx+1}.{image_format}"
                    image_path = os.path.join(image_output_dir, image_filename)

                    # Save image
                    with open(image_path, "wb") as f:
                        f.write(image_bytes)
                    images.append(image_path)

        result = {
            "text": "\n".join(text_runs),
            "images": images  # List of image file paths
        }
        return result
    except Exception as e:
        return f"PPTX Error: {str(e)}"



def parse_file(file, filetype):
    try:
        if filetype == "pdf":
            return parse_pdf(file)
        elif filetype == "txt":
            return parse_txt(file)
        elif filetype == "json":
            return parse_json(file)
        elif filetype == "csv":
            return parse_csv(file)
        elif filetype == "xlsx":
            return parse_xlsx(file)
        elif filetype == "pptx":
            return parse_pptx(file)
        else:
            return "Unsupported file type"
    except Exception as e:
        return f"Error parsing file: {e}"

