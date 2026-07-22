import logging

logger = logging.getLogger("ocr")


def ocr_image(path: str) -> str:
    """Run OCR on an image file. Returns empty string (never raises) if
    tesseract isn't installed on the host — the document still gets ingested,
    just without extracted text, and the upload response says so."""
    try:
        import pytesseract
        from PIL import Image

        img = Image.open(path)
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception as e:
        logger.warning("OCR failed for %s: %s", path, e)
        return ""
