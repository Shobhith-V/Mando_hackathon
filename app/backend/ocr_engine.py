import pytesseract
from PIL import Image
import io

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def ocr_image(file):
    image = Image.open(file)
    text = pytesseract.image_to_string(image)
    return text
