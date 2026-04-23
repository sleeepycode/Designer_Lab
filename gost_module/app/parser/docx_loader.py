from docx import Document


def load_docx(path: str) -> Document:
    return Document(path)
