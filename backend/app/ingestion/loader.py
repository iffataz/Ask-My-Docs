from pathlib import Path

from pydantic import BaseModel
from pypdf import PdfReader

TEXT_EXTENSIONS = {".md", ".txt"}
PDF_EXTENSIONS = {".pdf"}


class UnsupportedFileTypeError(ValueError):
    def __init__(self, suffix: str) -> None:
        super().__init__(f"Unsupported file type: {suffix!r}")
        self.suffix = suffix


class LoadedDocument(BaseModel):
    filename: str
    text: str


def _load_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def load_document(path: str | Path) -> LoadedDocument:
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix in PDF_EXTENSIONS:
        text = _load_pdf_text(path)
    elif suffix in TEXT_EXTENSIONS:
        text = path.read_text(encoding="utf-8")
    else:
        raise UnsupportedFileTypeError(suffix)

    return LoadedDocument(filename=path.name, text=text)
