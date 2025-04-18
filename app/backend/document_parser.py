import fitz  # PyMuPDF
import io
from PIL import Image
from backend.ocr_engine import ocr_image_bytes  

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

def parse_json(file):
    try:
        return file.read().decode("utf-8")  # You can later json.loads this
    except Exception as e:
        return f"Error parsing JSON: {e}"

def parse_file(file, filetype):
    try:
        if filetype == "pdf":
            return parse_pdf(file)
        elif filetype == "txt":
            return parse_txt(file)
        elif filetype == "json":
            return parse_json(file)
        else:
            return "Unsupported file type"
    except Exception as e:
        return f"Error parsing file: {e}"
