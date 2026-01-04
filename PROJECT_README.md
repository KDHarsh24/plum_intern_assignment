# Plum OPD Claim Adjudication System

An AI-powered web application that automates OPD insurance claim adjudication using **free and open-source tools** - no API keys required!

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────────────────────────────┐
│   React/Next.js │────▶│              FastAPI Backend            │
│    Frontend     │     │                                         │
└─────────────────┘     │  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
                        │  │   OCR   │  │   LLM   │  │  Rules  │ │
                        │  │Tesseract│  │ Ollama  │  │ Engine  │ │
                        │  └────┬────┘  └────┬────┘  └────┬────┘ │
                        │       │            │            │       │
                        │       └────────────┴────────────┘       │
                        │                    │                    │
                        │              ┌─────▼─────┐              │
                        │              │  SQLite   │              │
                        │              │  Database │              │
                        │              └───────────┘              │
                        └─────────────────────────────────────────┘
```

## 🛠️ Tech Stack (All Free & Open Source)

| Component | Technology | Why |
|-----------|------------|-----|
| **Backend** | Python FastAPI | Fast, modern, async support |
| **Frontend** | Next.js + Tailwind | React with great DX |
| **Database** | SQLite | Zero config, file-based |
| **OCR** | Tesseract | Free, open-source OCR |
| **LLM** | Ollama (Mistral/Llama) | Free local LLM inference |

## 📋 Prerequisites

1. **Python 3.9+** - [Download](https://www.python.org/downloads/)
2. **Node.js 18+** - [Download](https://nodejs.org/)
3. **Tesseract OCR** - [Windows Install Guide](https://github.com/UB-Mannheim/tesseract/wiki)
4. **Ollama** (Optional, for AI extraction) - [Download](https://ollama.ai/)

## 🚀 Quick Start

### 1. Install Tesseract OCR (Windows)

```powershell
# Download and install from:
# https://github.com/UB-Mannheim/tesseract/releases
# Default path: C:\Program Files\Tesseract-OCR\tesseract.exe
```

### 2. Install Ollama (Optional - for AI extraction)

```powershell
# Download from https://ollama.ai/download
# Then pull a model:
ollama pull mistral
# Or for better results:
ollama pull llama3
```

### 3. Setup Backend

```powershell
cd backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Setup Frontend

```powershell
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **API**: http://localhost:8000

## 📁 Project Structure

```
plum_intern_assignment/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration
│   │   ├── models.py            # Database models
│   │   ├── schemas.py           # Pydantic schemas
│   │   └── services/
│   │       ├── ocr_service.py   # Tesseract OCR
│   │       ├── llm_service.py   # Ollama LLM extraction
│   │       ├── adjudication_engine.py  # Rules engine
│   │       └── claim_processor.py      # Main processor
│   ├── requirements.txt
│   └── uploads/                 # Uploaded documents
├── frontend/
│   ├── src/app/
│   │   ├── page.tsx            # Claim submission
│   │   ├── claims/page.tsx     # Claims list
│   │   └── policy/page.tsx     # Policy info
│   └── package.json
├── policy_terms.json           # Policy configuration
├── adjudication_rules.md       # Business rules
└── test_cases.json            # Test scenarios
```

## 🔄 Claim Processing Flow

1. **Submit Claim** → User uploads documents + enters claim details
2. **OCR Extraction** → Tesseract extracts text from images/PDFs
3. **LLM Processing** → Ollama extracts structured data (or regex fallback)
4. **Adjudication** → Rules engine validates against policy
5. **Decision** → APPROVED / REJECTED / PARTIAL / MANUAL_REVIEW

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/claims/submit` | Submit new claim |
| POST | `/api/claims/{id}/process` | Process claim |
| GET | `/api/claims/{id}` | Get claim details |
| GET | `/api/claims` | List all claims |
| GET | `/api/policy` | Get policy terms |
| GET | `/api/stats` | Get statistics |

## ⚙️ Configuration

### Tesseract Path (Windows)
Edit `backend/app/config.py`:
```python
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

### Ollama Model
```python
OLLAMA_MODEL = "mistral"  # or "llama3", "phi3"
```

## 🧪 Testing

### Test Cases from `test_cases.json`:

| ID | Scenario | Expected Result |
|----|----------|-----------------|
| TC001 | Simple Consultation ₹1,500 | APPROVED ₹1,350 (10% copay) |
| TC002 | Dental ₹12,000 (whitening) | PARTIAL ₹8,000 (cosmetic excluded) |
| TC003 | Claim ₹7,500 | REJECTED (exceeds ₹5,000 limit) |
| TC004 | Missing prescription | REJECTED |
| TC005 | Diabetes (within 90 days) | REJECTED (waiting period) |
| TC006 | Ayurveda ₹4,000 | APPROVED |
| TC007 | MRI without pre-auth | REJECTED |
| TC008 | Multiple same-day claims | MANUAL_REVIEW |
| TC009 | Weight loss treatment | REJECTED (excluded) |
| TC010 | Network hospital ₹4,500 | APPROVED ₹3,600 (20% discount) |

## 🔧 Troubleshooting

### Tesseract not found
```powershell
# Verify installation
tesseract --version
# If not found, add to PATH or update config.py
```

### Ollama not running
```powershell
# Start Ollama
ollama serve
# Pull model if needed
ollama pull mistral
```

### Without Ollama
The system will fallback to regex-based extraction if Ollama is unavailable. This provides basic functionality but with lower accuracy.

## 📈 Evaluation Criteria Coverage

| Criteria | Implementation |
|----------|----------------|
| ✅ Document Processing | Tesseract OCR for images/PDFs |
| ✅ AI/LLM Integration | Ollama (Mistral/Llama) + regex fallback |
| ✅ Decision Engine | Complete rules from adjudication_rules.md |
| ✅ Data Storage | SQLite with SQLAlchemy ORM |
| ✅ User Interface | React/Next.js with Tailwind CSS |
| ✅ Confidence Scores | Extracted from OCR + LLM |
| ✅ Policy Validation | All rules from policy_terms.json |

## 🎥 Demo Video Outline

1. **Introduction** (1 min) - System overview
2. **Claim Submission** (2 min) - Upload & submit
3. **Processing** (2 min) - Show OCR + LLM extraction
4. **Decision Display** (2 min) - Results & reasoning
5. **Test Cases** (3 min) - Walk through 2-3 scenarios

## 📝 License

MIT License - Free to use and modify
