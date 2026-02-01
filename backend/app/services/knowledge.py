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


def split_text_into_chunks(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """
    遞迴分段：依序嘗試用段落、換行、句號、逗號切分，
    優先保留語意完整的段落結構。
    """
    separators = ["\n\n", "\n", "。", "！", "？", ".", "!", "?", "；", ";", "，", ",", " "]
    return _recursive_split(text.strip(), separators, chunk_size, overlap)


def _recursive_split(text: str, separators: list[str], chunk_size: int, overlap: int) -> list[str]:
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    # 找到第一個能切分文本的分隔符
    chosen_sep = None
    for sep in separators:
        if sep in text:
            chosen_sep = sep
            break

    # 沒有任何分隔符，硬切
    if chosen_sep is None:
        return _hard_split(text, chunk_size, overlap)

    # 用該分隔符切分
    parts = text.split(chosen_sep)

    # 合併小段落，確保每個 chunk 盡量接近 chunk_size
    chunks = []
    current = ""
    for part in parts:
        part = part.strip()
        if not part:
            continue

        candidate = f"{current}{chosen_sep}{part}" if current else part

        if len(candidate) <= chunk_size:
            current = candidate
        else:
            # 先保存當前累積的內容
            if current:
                chunks.append(current)
            # 如果單個 part 超過 chunk_size，用下一層分隔符遞迴切分
            if len(part) > chunk_size:
                sub_chunks = _recursive_split(part, separators[separators.index(chosen_sep) + 1:], chunk_size, overlap)
                chunks.extend(sub_chunks)
                current = ""
            else:
                current = part

    if current:
        chunks.append(current)

    # 加入 overlap：將前一個 chunk 的尾部加到下一個 chunk 的開頭
    if overlap > 0 and len(chunks) > 1:
        chunks = _add_overlap(chunks, overlap)

    return chunks


def _hard_split(text: str, chunk_size: int, overlap: int) -> list[str]:
    """沒有分隔符時的硬切分。"""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap if end < len(text) else end
    return chunks


def _add_overlap(chunks: list[str], overlap: int) -> list[str]:
    """在相鄰 chunk 之間加入重疊文字。"""
    result = [chunks[0]]
    for i in range(1, len(chunks)):
        prev_tail = chunks[i - 1][-overlap:]
        current = chunks[i]
        if not current.startswith(prev_tail):
            result.append(prev_tail + current)
        else:
            result.append(current)
    return result


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
