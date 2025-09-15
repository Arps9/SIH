from fastapi import FastAPI, File, UploadFile, Depends
import os
import pdfplumber
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from transformers import pipeline
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Document, Base
from fastapi.middleware.cors import CORSMiddleware

# ================== DB Setup ==================
Base.metadata.create_all(bind=engine)

# ================== FastAPI ==================
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for development, allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Upload folder
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# HuggingFace pipelines
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
ner_model = pipeline("ner", model="dslim/bert-base-NER", grouped_entities=True)

# ================== DB Dependency ==================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ================== OCR Helper ==================
def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    try:
        # Digital PDF
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted
    except Exception as e:
        print("pdfplumber failed:", e)

    # OCR fallback
    if not text.strip():
        print("No digital text found → OCR fallback")
        pages = convert_from_path(file_path, 300)
        for page in pages:
            text += pytesseract.image_to_string(page, lang="eng+mal")

    return text.strip()

# ================== Categorization ==================
# ================== Categorization ==================
def detect_category(text: str) -> str:
    text = text.lower()

    # Finance
    if "invoice" in text or "payment" in text or "salary" in text or "budget" in text:
        return "Finance"

    # Legal
    elif "legal" in text or "contract" in text or "agreement" in text or "compliance" in text:
        return "Legal"

    # Technical
    elif "technical" in text or "engineering" in text or "specification" in text or "design" in text:
        return "Technical"

    # HR
    elif "employee" in text or "leave" in text or "recruitment" in text or "policy" in text:
        return "HR"

    # General (default)
    else:
        return "General"



# ================== ROUTES ==================

# 1. Upload & extract text + categorize
@app.post("/upload/")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb") as f:
        f.write(await file.read())

    extracted_text = extract_text_from_pdf(file_location)
    category = detect_category(extracted_text)

    # Save to DB
    doc = Document(filename=file.filename, text=extracted_text, category=category)
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {
        "status": "success",
        "filename": file.filename,
        "category": category,
        "text_preview": extracted_text[:500],
    }

# 2. Summarize document
@app.post("/summarize/")
async def summarize(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb") as f:
        f.write(await file.read())

    extracted_text = extract_text_from_pdf(file_location)
    category = detect_category(extracted_text)

    summary = summarizer(extracted_text[:1000], max_length=150, min_length=40, do_sample=False)[0]['summary_text']

    # Update if exists, else insert
    doc = db.query(Document).filter(Document.filename == file.filename).first()
    if doc:
        doc.summary = summary
        doc.category = category
    else:
        doc = Document(filename=file.filename, text=extracted_text, summary=summary, category=category)
        db.add(doc)

    db.commit()
    db.refresh(doc)

    return {"status": "success", "filename": file.filename, "summary": summary, "category": category}

# 3. Extract entities
@app.post("/extract_entities/")
async def extract_entities(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb") as f:
        f.write(await file.read())

    extracted_text = extract_text_from_pdf(file_location)
    category = detect_category(extracted_text)

    entities = ner_model(extracted_text)
    entities_cleaned = [
        {"entity_group": e["entity_group"], "word": e["word"], "score": float(e["score"])}
        for e in entities
    ]

    # Update if exists, else insert
    doc = db.query(Document).filter(Document.filename == file.filename).first()
    if doc:
        doc.entities = ", ".join([e["word"] for e in entities])
        doc.category = category
    else:
        doc = Document(
            filename=file.filename,
            text=extracted_text,
            entities=", ".join([e["word"] for e in entities]),
            category=category,
        )
        db.add(doc)

    db.commit()
    db.refresh(doc)

    return {"status": "success", "filename": file.filename, "entities": entities_cleaned, "category": category}

# 4. Fetch all documents
@app.get("/documents/")
def get_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).all()
    return docs

# 5. Fetch by category
@app.get("/documents/{category}")
def get_documents_by_category(category: str, db: Session = Depends(get_db)):
    docs = db.query(Document).filter(Document.category == category).all()
    return docs
