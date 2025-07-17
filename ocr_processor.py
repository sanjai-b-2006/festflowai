import pytesseract
from PIL import Image
import re
import io

# --- IMPORTANT ---
# On Windows, you might need to set the path to the Tesseract executable.
# Uncomment and update the line below if you get a "Tesseract not found" error.
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
def process_receipt(image_file):
    """
    Uses OCR to extract amount, date, and potential vendor from a receipt image.
    Args:
        image_file: A file-like object (e.g., from st.file_uploader).
    Returns:
        A dictionary with extracted data: {'amount': float, 'date': str}.
    """
    try:
        image = Image.open(io.BytesIO(image_file.getvalue()))
        text = pytesseract.image_to_string(image)

        # Regex to find amounts (e.g., 12.34, 1,234.56, 1500)
        # This is a simple regex; more complex ones can be built for higher accuracy.
        amount_pattern = r'Total|Amount|TOTAL|AMOUNT|SUBTOTAL|Subtotal|Payable|PAYABLE'
        amounts = re.findall(r'(\d[\d,]*\.\d{2})', text)
        
        extracted_amount = 0.0
        if amounts:
            # Take the largest amount found, as it's likely the total
            float_amounts = [float(a.replace(',', '')) for a in amounts]
            extracted_amount = max(float_amounts)

        # You can add more regex for date, vendor name etc.
        # date_pattern = r'\d{2}/\d{2}/\d{4}'
        # dates = re.findall(date_pattern, text)
        # extracted_date = dates[0] if dates else None

        return {"amount": extracted_amount, "text": text}

    except Exception as e:
        print(f"OCR Error: {e}")
        return {"amount": 0.0, "text": "Could not process image."}