from PyPDF2 import PdfReader
from sqlalchemy.orm import Session
from ..models.knowledge import KnowledgeDocument
from .embedding import get_embeddings


def extract_text_from_pdf(file) -> str:
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text.strip()


def split_text_into_chunks(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap

    return chunks


def process_and_store(db: Session, title: str, text: str, filename: str | None = None) -> int:
    chunks = split_text_into_chunks(text)
    if not chunks:
        return 0

    embeddings = get_embeddings(chunks)

    docs = []
    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        doc = KnowledgeDocument(
            title=title,
            content=chunk,
            embedding=emb,
            source_filename=filename,
            chunk_index=i,
        )
        docs.append(doc)

    db.add_all(docs)
    db.commit()
    return len(docs)
