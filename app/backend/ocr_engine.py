import pytesseract
from PIL import Image
import io



def ocr_image(file):
    """For direct image uploads"""
    try:
        image = Image.open(file)
        return pytesseract.image_to_string(image)
    except Exception as e:
        return f"OCR Error: {str(e)}"

def ocr_image_bytes(image_bytes):
    """For images extracted from PDFs"""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(image)
    except Exception as e:
        return f"OCR Error: {str(e)}"