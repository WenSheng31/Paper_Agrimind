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

    # 優先在換行、句號等位置斷開
    separators = ["\n\n", "\n", "。", "！", "？", ".", "!", "?", "；", ";"]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size

        if end >= len(text):
            chunk = text[start:].strip()
            if chunk:
                chunks.append(chunk)
            break

        # 在 chunk_size 範圍內找最後一個分隔符
        best_break = -1
        for sep in separators:
            pos = text.rfind(sep, start, end)
            if pos > start and pos + len(sep) > best_break:
                best_break = pos + len(sep)

        if best_break > start:
            end = best_break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = max(end - overlap, start + 1)

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
