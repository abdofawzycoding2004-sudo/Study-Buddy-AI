import os
import PyPDF2
import docx
import chromadb
from chromadb.config import Settings
from django.conf import settings
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


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


def query_similar_chunks(question, n_results=3):
    client = get_chroma_client()
    collection = client.get_or_create_collection(name="teacher_documents")
    if collection.count() == 0:
        return []
    results = collection.query(
        query_texts=[question],
        n_results=n_results,
    )
    chunks = []
    if results and results['documents']:
        for i, doc in enumerate(results['documents'][0]):
            chunks.append({
                'text': doc,
                'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                'distance': results['distances'][0][i] if results['distances'] else 0,
            })
    return chunks


def get_llm_client():
    api_key = os.getenv('LLM_API_KEY')
    base_url = os.getenv('LLM_BASE_URL')
    if not api_key:
        raise ValueError("LLM_API_KEY environment variable is not set")
    kwargs = {'api_key': api_key}
    if base_url:
        kwargs['base_url'] = base_url
    return OpenAI(**kwargs)


def build_rag_prompt(question, chunks):
    context = "\n\n".join([c['text'] for c in chunks])
    return (
        "You are an AI tutor. Answer the student's question using ONLY the following context "
        "from their teacher's curriculum. If the answer is not in the context, say you don't know.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}"
    )


def ask_llm_stream(question, chunks):
    client = get_llm_client()
    prompt = build_rag_prompt(question, chunks)
    model = os.getenv('LLM_MODEL', 'gpt-4o-mini')
    stream = client.chat.completions.create(
        model=model,
        messages=[{'role': 'user', 'content': prompt}],
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else ''
        if delta:
            yield delta
