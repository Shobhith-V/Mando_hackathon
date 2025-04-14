import pytesseract
from PIL import Image
import io

def ocr_image(file):
    image = Image.open(file)
    text = pytesseract.image_to_string(image)
    return text
