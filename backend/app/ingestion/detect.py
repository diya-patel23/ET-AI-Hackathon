EXTENSION_MAP = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".doc": "docx",
    ".xlsx": "xlsx",
    ".xls": "xlsx",
    ".csv": "csv",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".tiff": "image",
    ".bmp": "image",
    ".txt": "txt",
    ".eml": "email",
}


def detect_file_type(filename: str) -> str:
    lower = filename.lower()
    for ext, ftype in EXTENSION_MAP.items():
        if lower.endswith(ext):
            return ftype
    return "unknown"
