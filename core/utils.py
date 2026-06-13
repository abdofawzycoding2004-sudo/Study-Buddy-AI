import os
import json
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
        "You are an AI tutor. The student has curriculum documents uploaded by their teacher. "
        "Use the following context to answer if relevant. If not, use your own knowledge to give a helpful answer.\n\n"
        f"Context from curriculum:\n{context}\n\n"
        f"Student question: {question}"
    )


def build_general_prompt(question):
    return (
        "You are an AI tutor helping a student. Answer their question thoroughly and clearly. "
        f"\n\nStudent question: {question}"
    )


def ask_llm_stream(question, chunks):
    client = get_llm_client()
    if chunks:
        prompt = build_rag_prompt(question, chunks)
    else:
        prompt = build_general_prompt(question)
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


def generate_quiz(num_questions, difficulty, question_type, chunks=None):
    client = get_llm_client()
    if chunks:
        context = "\n\n".join([c['text'] for c in chunks])
        prompt = (
            f"You are an AI tutor. Generate {num_questions} {question_type} questions "
            f"of {difficulty} difficulty based on the following curriculum context. "
            "Make them thoughtful and educational, testing real understanding. "
            "Return a valid JSON array only, no other text. "
            "Each item must have: 'question' (string), 'correct_answer' (string). "
        )
        if question_type == 'multiple_choice':
            prompt += (
                "Include 'options' (array of 4 strings) for each question. "
                "The correct_answer must match one of the options exactly."
            )
        prompt += f"\n\nContext:\n{context}"
    else:
        prompt = (
            f"You are an AI tutor. Generate {num_questions} {question_type} questions "
            f"of {difficulty} difficulty on general academic subjects (science, math, history, language, geography). "
            "Make them thoughtful and educational, testing real understanding, not trivial facts. "
            "Return a valid JSON array only, no other text. "
            "Each item must have: 'question' (string), 'correct_answer' (string). "
        )
        if question_type == 'multiple_choice':
            prompt += (
                "Include 'options' (array of 4 strings) for each question. "
                "Make the distractors plausible. The correct_answer must match one of the options exactly."
            )
        prompt += " Ensure questions are appropriate for a middle school or high school level."

    model = os.getenv('LLM_MODEL', 'gpt-4o-mini')
    resp = client.chat.completions.create(
        model=model,
        messages=[{'role': 'user', 'content': prompt}],
        temperature=0.7,
    )
    content = resp.choices[0].message.content.strip()
    if content.startswith('```'):
        content = content.split('\n', 1)[-1]
        content = content.rsplit('```', 1)[0]
    return json.loads(content)


def grade_short_answer(question, correct_answer, student_answer):
    client = get_llm_client()
    prompt = (
        f"Question: {question}\n"
        f"Correct answer: {correct_answer}\n"
        f"Student answer: {student_answer}\n\n"
        "Evaluate the student's answer. Return a valid JSON object only, no other text: "
        '{"correct": boolean, "feedback": "brief explanation"}'
    )
    model = os.getenv('LLM_MODEL', 'gpt-4o-mini')
    resp = client.chat.completions.create(
        model=model,
        messages=[{'role': 'user', 'content': prompt}],
        temperature=0.3,
    )
    content = resp.choices[0].message.content.strip()
    if content.startswith('```'):
        content = content.split('\n', 1)[-1]
        content = content.rsplit('```', 1)[0]
    return json.loads(content)
