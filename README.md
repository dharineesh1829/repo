# ResumeMatch AI
### AI Resume & Job Matching + Mock Interview Platform

> **"Know Your Fit. Improve Your Skills. Ace Your Interview."**

ResumeMatch AI is a modern, responsive, full-stack web application designed to evaluate candidate resumes against employer job descriptions, calculate algorithmic job readiness scores, uncover critical skill gaps with actionable learning roadmaps, and generate dynamic AI-powered mock interviews with rubric-based answer evaluations and printable readiness reports.

---

## 🌟 Key Features

1. **Multi-Format Document Parsing**:
   - Ingests **PDF**, **DOCX**, and **TXT** files or direct raw text.
   - Text sanitization, null-byte stripping, and file integrity validation (up to 10MB).
2. **AI & NLP Extraction Engine**:
   - Extracts candidate experience, skills, education, certifications, and technical projects.
   - Extracts job requirements: core skills, min/preferred experience, education tier, and key duties.
3. **5-Pillar Deterministic Matching Engine**:
   - Mathematical, transparent scoring from 0 to 100% without synthetic or random numbers.
   - Separate transparent scores for **Skill Match (40%)**, **Experience Match (25%)**, **Education Match (15%)**, **Certification Match (10%)**, and **Responsibility Match (10%)**.
4. **Eligibility Analysis**:
   - Categorizes status as **Eligible**, **Partially Eligible**, or **Not Eligible**.
   - Itemized checklist with clear explanations for education, experience, and core skill requirements.
5. **Skill Gap Analysis & Learning Roadmaps**:
   - Distinguishes **Matched**, **Missing**, **Partially Matched**, and **Recommended** skills.
   - Every missing skill includes: Importance, Why It Is Required, Learning Direction, Difficulty Level, and Estimated Priority (P1/P2/P3).
6. **Dynamic Mock Interview Chamber**:
   - Generates contextual questions across 5 categories: **HR**, **Technical**, **Behavioral (STAR)**, **Resume-Based**, and **Job-Description-Specific**.
   - Live timer, question progress track, speech-to-text dictation (Web Speech API), and word counter.
7. **Rubric-Based AI Answer Evaluation**:
   - Scores responses on **Technical Accuracy (/10)**, **Relevance (/10)**, **Completeness (/10)**, and **Communication (/10)**.
   - Provides confidence indicators, missing concepts, "What You Did Well", "What You Can Improve", and a model STAR answer approach.
8. **Final Preparation Report & Interactive Checklist**:
   - Candidate summary, readiness topics, and checkable preparation items.
   - High-contrast, printable/downloadable **PDF export** via standard browser print dialog.
9. **Zero-API-Key Demo Mode**:
   - Instant 1-click demonstration preloaded with a sample Machine Learning Engineer resume and job description.

---

## 📁 Project Architecture & Directory Structure

```
c:\resume jd\
├── app\
│   ├── __init__.py              # Application package marker
│   ├── main.py                  # FastAPI router, endpoints & static mounting
│   ├── config.py                # Environment configurations (.env)
│   ├── database.py              # SQLite database manager & CRUD operations
│   ├── models\
│   │   ├── __init__.py
│   │   └── schemas.py           # Pydantic data schemas & contracts
│   ├── services\
│   │   ├── __init__.py
│   │   ├── document_parser.py   # PDF (pypdf), DOCX (python-docx), TXT parser
│   │   ├── matching_engine.py   # 5-pillar scoring, eligibility, gap analysis
│   │   ├── ai_service.py        # OpenAI/Gemini adapter & NLP rule engine
│   │   └── interview_service.py # Interview sessions, evaluation & reports
│   └── static\
│       ├── index.html           # SPA Dashboard with all 10 interactive views
│       ├── css\
│       │   ├── style.css        # Modern AI SaaS dark theme (Obsidian/Cyan)
│       │   └── print.css        # Clean, high-contrast PDF print stylesheet
│       └── js\
│           ├── api.js           # REST API client wrapper
│           ├── demo_data.js     # Preloaded sample resume & JD data
│           └── app.js           # Navigation, speech recognition & state manager
├── demo_files\
│   ├── sample_resume.txt        # Demo resume (Alex Chen, ML & Dev)
│   ├── sample_resume.docx       # Word document version
│   ├── sample_job_description.txt # Demo JD (Machine Learning Engineer)
│   └── sample_job_description.docx# Word document version
├── requirements.txt             # Python dependencies
├── .env.example                 # Example environment variables
├── run.py                       # One-click execution launcher
└── README.md                    # Project documentation
```

---

## 🚀 1. How to Run the Project Locally

### Prerequisites
- **Python 3.10+** (Tested on Python 3.14)
- **pip** package manager

### Steps:
1. **Clone or Open the Repository**:
   ```powershell
   cd "c:\resume jd"
   ```

2. **Install Dependencies**:
   ```powershell
   python -m pip install -r requirements.txt
   ```

3. **Launch the Application**:
   ```powershell
   python run.py
   ```
   *Or alternatively via uvicorn directly:*
   ```powershell
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

4. **Access the Dashboard**:
   Open your browser and navigate to:
   👉 **`http://127.0.0.1:8000`**

---

## 🔑 2. How to Configure the AI API Key

ResumeMatch AI features a **Dual AI Engine Architecture**:
- If no API key is provided, it automatically utilizes the built-in deterministic **NLP & Rule Engine** (Demo Mode).
- To connect a live Large Language Model (e.g. OpenAI or Gemini):

1. Copy `.env.example` to a new file named `.env`:
   ```powershell
   cp .env.example .env
   ```
2. Open `.env` and enter your OpenAI or Gemini key:
   ```env
   OPENAI_API_KEY=sk-proj-your-openai-key-here
   # Optional: default is gpt-4o-mini
   OPENAI_MODEL=gpt-4o-mini

   # Or Gemini:
   GEMINI_API_KEY=your-gemini-api-key-here
   ```
3. Restart `python run.py`. The top/sidebar status will automatically reflect **`Live AI (gpt-4o-mini)`**.

---

## ⚡ 3. How to Use Demo Mode

You can test the entire application end-to-end without uploading any files:
1. Open the homepage at `http://127.0.0.1:8000`.
2. Click the **`⚡ Try Demo`** button in the hero section or top header.
3. The platform will:
   - Ingest the preloaded Machine Learning candidate resume (*Alex Chen*).
   - Ingest the CloudScale AI Machine Learning Engineer job description.
   - Run the 5-pillar matching engine and eligibility calculation.
   - Populate the **Dashboard**, **Job Match**, **Skill Gap**, **Job Fit Report**, and generate 8 personalized **Mock Interview** questions.
4. You can practice answering questions, view instant AI evaluations, and export the final report to PDF.

---

## 📐 4. How the Matching Score is Calculated

The Overall Match Score is calculated using a transparent weighted composite formula:

$$\text{Overall Score} = 0.40 \times S + 0.25 \times E + 0.15 \times D + 0.10 \times C + 0.10 \times R$$

### Pillar Weights:
1. **Skill Match Score ($S$, 40% Weight)**:
   - Matches candidate skills against required JD skills with synonym resolution (e.g., *ReactJS = React*, *K8s = Kubernetes*).
   - Full credit (1.0) for exact matches; partial credit (0.6) for transferable skills (e.g., *Linux/APIs* transferring toward *AWS/Docker*).
   - $S = \min\left(100, \frac{\text{Matched} \times 1.0 + \text{Partial} \times 0.6}{\text{Total Required Skills}} \times 100\right)$
2. **Experience Match Score ($E$, 25% Weight)**:
   - Compares candidate tenure years against employer minimum required years.
   - If Candidate Years $\ge$ Required Years: 100%.
   - If Candidate Years $<$ Required Years: Scaled proportionally with bonus credit for demonstrated complex projects.
3. **Education Match Score ($D$, 15% Weight)**:
   - Evaluates degree hierarchy: PhD (5) $>$ Master's (4) $>$ Bachelor's (3) $>$ Diploma (2) $>$ High School (1).
   - If candidate degree level $\ge$ requirement: 100%. One tier below: 80%.
4. **Certification Match Score ($C$, 10% Weight)**:
   - Evaluates mandatory or preferred industry certifications. If no specific certs are required, having candidate certs awards 100%.
5. **Responsibility Overlap Score ($R$, 10% Weight)**:
   - Semantic token overlap and action verb alignment between candidate project descriptions and employer responsibilities.

### Eligibility Decision Rules:
- **Eligible**: All minimum requirements satisfied and Overall Score $\ge 70\%$.
- **Partially Eligible**: Foundational requirements satisfied, with a minor experience or tooling gap (Score between 50% and 70%).
- **Not Eligible**: Critical degree missing, massive experience gap ($>75\%$), or Score $< 50\%$.

---

## 🔒 5. How to Add User Authentication Later

The codebase was architected from day one to support authentication:
1. **Database Ready**:
   - The `users` table already exists in `app/database.py` with an `id`, `email`, and `created_at`.
   - The `analyses` table contains a foreign key `user_id` referencing `users(id)`.
2. **Implementation Strategy**:
   - Install `python-jose[cryptography]` and `passlib[bcrypt]`.
   - Add `/api/auth/register` and `/api/auth/login` endpoints returning a JWT token.
   - Add a FastAPI dependency `get_current_user(token: str = Depends(oauth2_scheme))` in `app/main.py`.
   - Replace the `"default_user"` fallback with `current_user.id` in all analysis CRUD calls.

---

## 🌐 6. How to Deploy the Application

### Option A: Render / Railway (PaaS)
1. Push this repository to GitHub.
2. In Render or Railway, create a **Web Service** connected to your repo.
3. Set the **Build Command**: `pip install -r requirements.txt`
4. Set the **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables: `OPENAI_API_KEY`, etc.

### Option B: Docker Container
Create a `Dockerfile` in the root:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
Build and run:
```bash
docker build -t resumematch-ai .
docker run -p 8000:8000 -e OPENAI_API_KEY="your-key" resumematch-ai
```

---

## 📚 API Reference Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Health status and LLM availability check |
| `POST` | `/api/upload/resume` | Upload resume file or paste raw text |
| `POST` | `/api/upload/jd` | Upload JD file or paste raw text |
| `POST` | `/api/match/{id}` | Execute 5-pillar comparison and eligibility analysis |
| `POST` | `/api/demo/load` | 1-Click loading of full demo dataset |
| `GET` | `/api/analyses` | List past candidate analysis sessions |
| `GET` | `/api/analysis/{id}` | Retrieve full analysis details |
| `DELETE` | `/api/analysis/{id}` | Delete analysis session and data |
| `GET` | `/api/interview/{id}` | Fetch personalized mock interview questions |
| `POST` | `/api/interview/submit` | Submit candidate answer for AI rubric evaluation |
| `GET` | `/api/interview/{id}/report` | Retrieve Final Preparation Report & Checklist |
