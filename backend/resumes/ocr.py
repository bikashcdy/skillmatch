"""Reading photos and scanned resumes with OCR (Tesseract).

Photos are cleaned up first (rotation from the camera, grey scale, enlargement, contrast, sharpening),
then read with more than one page-layout mode and the best result is kept. Scanned PDFs are read page by
page: a page that has real text is used as it is, a page that is only a picture is rendered and OCR'd.
"""

import io
import os
import re

MIN_PAGE_CHARS = 40  # a PDF page with fewer characters than this is treated as a picture
MAX_OCR_PAGES = 5  # resumes are short; this keeps a scanned book from running for minutes
TARGET_WIDTH = 2000  # photos narrower than this are enlarged, which helps Tesseract a lot
MAX_SIDE = 3500  # huge phone photos are shrunk to this
INSTALL_HELP = (
    "Install the Tesseract OCR program (Windows: https://github.com/UB-Mannheim/tesseract/wiki, keep the default "
    "folder) and restart the server, or upload a PDF/DOCX that contains real text."
)


class OCRUnavailable(ValueError):
    """OCR is needed but the libraries or the Tesseract program are missing."""


def _tesseract():
    try:
        import pytesseract
        from PIL import Image  # noqa: F401
    except ImportError as e:
        raise OCRUnavailable(
            "Text recognition (OCR) is not installed. Run: pip install -r requirements.txt. " + INSTALL_HELP
        ) from e
    cmd = os.environ.get("TESSERACT_CMD")
    if not cmd and os.name == "nt":
        default = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        cmd = default if os.path.exists(default) else None
    if cmd:
        pytesseract.pytesseract.tesseract_cmd = cmd
    return pytesseract


def ocr_status():
    """{"available": bool, "message": str} - shown to candidates so they know photos are supported."""
    try:
        pytesseract = _tesseract()
        version = pytesseract.get_tesseract_version()
        return {"available": True, "message": f"Photo and scanned resumes are supported (Tesseract {version})."}
    except OCRUnavailable as e:
        return {"available": False, "message": str(e)}
    except Exception:  # TesseractNotFoundError and friends
        return {"available": False, "message": "The Tesseract OCR program was not found. " + INSTALL_HELP}


def preprocess(image):
    """Make a photo easier to read: upright, grey, big enough, high contrast, sharp."""
    from PIL import Image, ImageFilter, ImageOps

    image = ImageOps.exif_transpose(image)  # phone photos store their rotation in metadata
    image = image.convert("L")
    width, height = image.size
    if max(width, height) > MAX_SIDE:
        scale = MAX_SIDE / max(width, height)
        image = image.resize((int(width * scale), int(height * scale)), Image.LANCZOS)
    elif width < TARGET_WIDTH:
        scale = min(TARGET_WIDTH / width, 3)
        image = image.resize((int(width * scale), int(height * scale)), Image.LANCZOS)
    image = ImageOps.autocontrast(image, cutoff=1)
    return image.filter(ImageFilter.SHARPEN)


def _score(text):
    """How much real text did a reading find? (count of words made of letters)"""
    return len(re.findall(r"[A-Za-z]{2,}", text))


def ocr_image(image):
    """Read text from a PIL image. Tries the normal layout first, then block / sparse layouts."""
    pytesseract = _tesseract()
    prepared = preprocess(image)
    best = ""
    try:
        for psm in (3, 6, 11):  # automatic layout, one uniform block, sparse text
            text = pytesseract.image_to_string(prepared, config=f"--oem 3 --psm {psm}")
            if _score(text) > _score(best):
                best = text
            if _score(best) >= 40:  # clearly a readable page, no need to try more
                break
    except pytesseract.TesseractNotFoundError as e:
        raise OCRUnavailable("The Tesseract OCR program was not found. " + INSTALL_HELP) from e
    return best


def _render_pages(path):
    """Render PDF pages to images with pypdfium2 (a pip package, no Poppler needed). None if unavailable."""
    try:
        import pypdfium2 as pdfium
    except ImportError:
        return None
    pdf = pdfium.PdfDocument(path)
    try:
        for index in range(min(len(pdf), MAX_OCR_PAGES)):
            yield index, pdf[index].render(scale=300 / 72).to_pil()  # 300 dpi
    finally:
        pdf.close()


def _embedded_images(page):
    from PIL import Image

    for embedded in page.images:
        yield Image.open(io.BytesIO(embedded.data))


def read_pdf(path):
    """Text of a PDF, using OCR for any page that is only a picture (scans, photos saved as PDF)."""
    from pypdf import PdfReader

    reader = PdfReader(path)
    page_texts = [(page.extract_text() or "") for page in reader.pages]
    picture_pages = [i for i, t in enumerate(page_texts) if len(t.strip()) < MIN_PAGE_CHARS]
    if not picture_pages:
        return "\n".join(page_texts)

    rendered = {}
    renderer = _render_pages(path)
    if renderer is not None:
        rendered = {i: img for i, img in renderer if i in picture_pages}
    for i in picture_pages[:MAX_OCR_PAGES]:
        if i in rendered:
            page_texts[i] = ocr_image(rendered[i])
        else:  # fallback: the pictures embedded in the page
            page_texts[i] = "\n".join(ocr_image(img) for img in _embedded_images(reader.pages[i]))
    return "\n".join(page_texts)


def read_image_file(path):
    from PIL import Image

    return ocr_image(Image.open(path))
