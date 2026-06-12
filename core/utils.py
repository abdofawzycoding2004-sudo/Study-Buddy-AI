import os
import PyPDF2
import docx
import chromadb
from chromadb.config import Settings
from django.conf import settings


def extract_text_from_pdf(file_path):
    text = ""
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text


def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs])


def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext in ('.docx', '.doc'):
        return extract_text_from_docx(file_path)
    raise ValueError(f"Unsupported file type: {ext}")


def chunk_text(text, chunk_size=500, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap
    return chunks


def get_chroma_client():
    persist_dir = settings.BASE_DIR / 'chroma_db'
    os.makedirs(persist_dir, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(persist_dir),
        settings=Settings(anonymized_telemetry=False),
    )


def store_document_chunks(document, chunks):
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name="teacher_documents",
        metadata={"hnsw:space": "cosine"},
    )

    ids = []
    embeddings_list = []
    metadatas = []
    documents = []

    for i, chunk in enumerate(chunks):
        chunk_id = f"doc_{document.id}_chunk_{i}"
        ids.append(chunk_id)
        documents.append(chunk)
        metadatas.append({
            "teacher_id": str(document.teacher_id),
            "document_id": str(document.id),
            "document_title": document.title,
            "chunk_index": i,
        })

    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
    )

    return len(chunks)
