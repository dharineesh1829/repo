"""
FastAPI application entry point for ResumeMatch AI.
Provides REST APIs for document upload, parsing, comparison, mock interviews,
and serves the modern AI SaaS dashboard frontend.
"""
import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import HOST, PORT, is_llm_available, OPENAI_MODEL, is_supabase_available, SUPABASE_URL
from app.database import (
    init_db, create_analysis, update_analysis, get_analysis,
    list_analyses, delete_analysis, get_interview_session,
    get_interview_session_by_analysis, get_preparation_report
)
from app.services.document_parser import extract_document_text, DocumentParsingError
from app.services.ai_service import parse_resume, parse_job_description
from app.services.matching_engine import compare_resume_to_jd
from app.services.interview_service import (
    start_or_get_interview_session, submit_candidate_answer,
    generate_final_preparation_report
)
from app.services.supabase_service import (
    check_connection as check_supabase_conn,
    save_employee_to_supabase,
    save_questions_to_supabase,
    save_performance_to_supabase,
    get_supabase_employee_data,
    get_supabase_questions,
    get_supabase_performance,
    sync_all_from_sqlite_to_supabase
)

from app.models.schemas import (
    ResumeInformation, JobRequirements, MatchResult,
    TextUploadRequest, SubmitAnswerRequest
)

# Initialize app
app = FastAPI(
    title="ResumeMatch AI API",
    description="AI Resume & Job Matching + Mock Interview Platform Backend",
    version="1.0.0"
)

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "app" / "static"

# Ensure database tables exist
init_db()

# =======================================================
# Core Application Endpoints
# =======================================================

@app.get("/api/health")
async def health_check():
    return {
        "status": "online",
        "llm_available": is_llm_available(),
        "model": OPENAI_MODEL if is_llm_available() else "NLP Rule Engine (Demo)",
        "supabase_configured": is_supabase_available(),
        "supabase_url": SUPABASE_URL if is_supabase_available() else None,
        "static_dir_exists": STATIC_DIR.exists()
    }

@app.get("/api/analyses")
async def get_all_analyses():
    """Returns list of past user analyses."""
    return list_analyses()

@app.get("/api/analysis/{analysis_id}")
async def get_single_analysis(analysis_id: str):
    """Retrieves full state of a specific analysis."""
    data = get_analysis(analysis_id)
    if not data:
        raise HTTPException(status_code=404, detail="Analysis session not found.")
    return data

@app.delete("/api/analysis/{analysis_id}")
async def remove_analysis(analysis_id: str):
    """Deletes analysis session and associated data."""
    success = delete_analysis(analysis_id)
    if not success:
        raise HTTPException(status_code=404, detail="Analysis session not found or already deleted.")
    return {"status": "success", "message": "Analysis deleted."}

# =======================================================
# Upload & Document Parsing Endpoints
# =======================================================

@app.post("/api/upload/resume")
async def upload_resume(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    analysis_id: Optional[str] = Form(None)
):
    """Uploads resume via file (PDF, DOCX, TXT) or raw text."""
    try:
        raw_text = ""
        filename = "pasted_resume.txt"
        
        if file and file.filename:
            filename = file.filename
            contents = await file.read()
            raw_text, _ = extract_document_text(filename, contents)
        elif text and text.strip():
            raw_text = text.strip()
        else:
            raise HTTPException(status_code=400, detail="No resume file or text content provided.")
        
        # Parse resume through AI / NLP engine
        parsed_resume, engine_used = await parse_resume(raw_text)
        
        # Create or update analysis record
        if not analysis_id:
            analysis_id = create_analysis(
                title=f"{parsed_resume.candidate_name}'s Analysis",
                resume_raw=raw_text,
                resume_filename=filename
            )
        
        update_analysis(
            analysis_id,
            resume_raw=raw_text,
            resume_filename=filename,
            resume_parsed=parsed_resume.model_dump()
        )
        
        # Sync employee/candidate record to Supabase
        try:
            full_a = get_analysis(analysis_id) or {}
            save_employee_to_supabase(
                analysis_id=analysis_id,
                title=full_a.get("title", f"{parsed_resume.candidate_name}'s Analysis"),
                resume_raw=raw_text,
                resume_filename=filename,
                resume_parsed=parsed_resume.model_dump(),
                jd_raw=full_a.get("jd_raw", ""),
                jd_filename=full_a.get("jd_filename", ""),
                jd_parsed=full_a.get("jd_parsed")
            )
        except Exception:
            pass
        
        return {
            "status": "success",
            "analysis_id": analysis_id,
            "filename": filename,
            "engine_used": engine_used,
            "parsed_data": parsed_resume.model_dump()
        }
    except DocumentParsingError as de:
        raise HTTPException(status_code=400, detail=str(de))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")

@app.post("/api/upload/jd")
async def upload_job_description(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    analysis_id: Optional[str] = Form(None)
):
    """Uploads Job Description via file (PDF, DOCX, TXT) or raw text."""
    try:
        raw_text = ""
        filename = "pasted_job_description.txt"
        
        if file and file.filename:
            filename = file.filename
            contents = await file.read()
            raw_text, _ = extract_document_text(filename, contents)
        elif text and text.strip():
            raw_text = text.strip()
        else:
            raise HTTPException(status_code=400, detail="No job description file or text content provided.")
        
        # Parse JD through AI / NLP engine
        parsed_jd, engine_used = await parse_job_description(raw_text)
        
        # Create or update analysis record
        if not analysis_id:
            analysis_id = create_analysis(
                title=f"Role: {parsed_jd.job_title}",
                jd_raw=raw_text,
                jd_filename=filename
            )
        
        update_analysis(
            analysis_id,
            jd_raw=raw_text,
            jd_filename=filename,
            jd_parsed=parsed_jd.model_dump()
        )
        
        # Sync employee/candidate record to Supabase
        try:
            full_a = get_analysis(analysis_id) or {}
            save_employee_to_supabase(
                analysis_id=analysis_id,
                title=full_a.get("title", f"Role: {parsed_jd.job_title}"),
                resume_raw=full_a.get("resume_raw", ""),
                resume_filename=full_a.get("resume_filename", ""),
                resume_parsed=full_a.get("resume_parsed"),
                jd_raw=raw_text,
                jd_filename=filename,
                jd_parsed=parsed_jd.model_dump()
            )
        except Exception:
            pass
        
        return {
            "status": "success",
            "analysis_id": analysis_id,
            "filename": filename,
            "engine_used": engine_used,
            "parsed_data": parsed_jd.model_dump()
        }
    except DocumentParsingError as de:
        raise HTTPException(status_code=400, detail=str(de))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing job description: {str(e)}")

# =======================================================
# Matching & Comparison Endpoint
# =======================================================

@app.post("/api/match/{analysis_id}")
async def execute_match(analysis_id: str):
    """Executes the 5-pillar matching engine and eligibility analysis."""
    analysis = get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis session not found.")
    
    if not analysis.get("resume_parsed"):
        raise HTTPException(status_code=400, detail="No resume uploaded yet for this analysis.")
    if not analysis.get("jd_parsed"):
        raise HTTPException(status_code=400, detail="No job description provided yet for this analysis.")
    
    resume = ResumeInformation(**analysis["resume_parsed"])
    jd = JobRequirements(**analysis["jd_parsed"])
    
    engine_type = "LIVE_LLM" if is_llm_available() else "NLP_RULE_ENGINE"
    match_result: MatchResult = compare_resume_to_jd(resume, jd, engine_type)
    
    update_analysis(
        analysis_id,
        match_result=match_result.model_dump()
    )
    
    # Pre-generate or update interview session
    session = await start_or_get_interview_session(analysis_id, resume, jd)

    # Sync Questions & Performance to Supabase
    try:
        save_questions_to_supabase(analysis_id, session.questions)
        save_performance_to_supabase(
            analysis_id=analysis_id,
            candidate_name=resume.candidate_name,
            job_title=jd.job_title,
            match_result=match_result.model_dump(),
            interview_session=session.model_dump(),
            preparation_report=get_preparation_report(analysis_id)
        )
    except Exception:
        pass

    return {
        "status": "success",
        "analysis_id": analysis_id,
        "match_result": match_result.model_dump()
    }

# =======================================================
# 1-Click Demo Mode Loader
# =======================================================

@app.post("/api/demo/load")
async def load_demo_data():
    """
    Loads sample demo data matching exact prompt specifications:
    Sample Resume:
    - Python, Java, SQL, Machine Learning, React, Git, TensorFlow, 1 internship, Bachelor's degree, 2 projects.
    Sample Job:
    - Python, Machine Learning, SQL, AWS, Docker, Git, 2+ years experience, Bachelor's degree.
    """
    demo_resume_path = BASE_DIR / "demo_files" / "sample_resume.txt"
    demo_jd_path = BASE_DIR / "demo_files" / "sample_job_description.txt"

    resume_text = demo_resume_path.read_text(encoding="utf-8") if demo_resume_path.exists() else ""
    jd_text = demo_jd_path.read_text(encoding="utf-8") if demo_jd_path.exists() else ""

    # Parse both
    parsed_resume, resume_engine = await parse_resume(resume_text)
    parsed_jd, jd_engine = await parse_job_description(jd_text)

    analysis_id = create_analysis(
        title="Demo: Alex Chen → ML & Software Engineer",
        resume_raw=resume_text,
        resume_filename="sample_resume.txt (Demo Data)",
        jd_raw=jd_text,
        jd_filename="sample_job_description.txt (Demo Data)"
    )

    update_analysis(
        analysis_id,
        resume_parsed=parsed_resume.model_dump(),
        jd_parsed=parsed_jd.model_dump()
    )

    # Run match
    match_result = compare_resume_to_jd(parsed_resume, parsed_jd, engine_type="NLP_RULE_ENGINE (Demo Data)")
    update_analysis(analysis_id, match_result=match_result.model_dump())

    # Create interview session
    interview_session = await start_or_get_interview_session(analysis_id, parsed_resume, parsed_jd)

    # Also generate initial preparation report
    prep_report = generate_final_preparation_report(
        analysis_id=analysis_id,
        resume=parsed_resume,
        jd=parsed_jd,
        match_result=match_result,
        session=interview_session
    )

    # Sync Demo Data into Supabase: Employee, Questions, and Performance Details
    try:
        save_employee_to_supabase(
            analysis_id=analysis_id,
            title="Demo: Alex Chen → ML & Software Engineer",
            resume_raw=resume_text,
            resume_filename="sample_resume.txt (Demo Data)",
            resume_parsed=parsed_resume.model_dump(),
            jd_raw=jd_text,
            jd_filename="sample_job_description.txt (Demo Data)",
            jd_parsed=parsed_jd.model_dump()
        )
        save_questions_to_supabase(analysis_id, interview_session.questions)
        save_performance_to_supabase(
            analysis_id=analysis_id,
            candidate_name=parsed_resume.candidate_name,
            job_title=parsed_jd.job_title,
            match_result=match_result.model_dump(),
            interview_session=interview_session.model_dump(),
            preparation_report=prep_report.model_dump()
        )
    except Exception:
        pass

    return {
        "status": "success",
        "analysis_id": analysis_id,
        "is_demo": True,
        "resume": parsed_resume.model_dump(),
        "job_description": parsed_jd.model_dump(),
        "match_result": match_result.model_dump(),
        "interview_session": interview_session.model_dump(),
        "preparation_report": prep_report.model_dump()
    }

# =======================================================
# Mock Interview Endpoints
# =======================================================

@app.get("/api/interview/{analysis_id}")
async def get_interview_for_analysis(analysis_id: str):
    """Fetches or generates interview session for this analysis."""
    analysis = get_analysis(analysis_id)
    if not analysis or not analysis.get("resume_parsed") or not analysis.get("jd_parsed"):
        raise HTTPException(status_code=400, detail="Analysis with parsed resume and JD is required.")
    
    resume = ResumeInformation(**analysis["resume_parsed"])
    jd = JobRequirements(**analysis["jd_parsed"])
    session = await start_or_get_interview_session(analysis_id, resume, jd)
    return session.model_dump()

@app.post("/api/interview/submit")
async def submit_answer(payload: SubmitAnswerRequest):
    """Submits candidate answer for AI evaluation."""
    try:
        result = await submit_candidate_answer(
            session_id=payload.session_id,
            question_id=payload.question_id,
            answer_text=payload.answer_text,
            time_spent_seconds=payload.time_spent_seconds
        )
        return {"status": "success", **result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/interview/{analysis_id}/report")
async def get_interview_report(analysis_id: str):
    """Generates and returns the Final Preparation Report."""
    analysis = get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    
    report = get_preparation_report(analysis_id)
    if not report:
        if not analysis.get("resume_parsed") or not analysis.get("jd_parsed") or not analysis.get("match_result"):
            raise HTTPException(status_code=400, detail="Full analysis and match required to generate report.")
        
        resume = ResumeInformation(**analysis["resume_parsed"])
        jd = JobRequirements(**analysis["jd_parsed"])
        match_res = MatchResult(**analysis["match_result"])
        
        session_data = get_interview_session_by_analysis(analysis_id)
        session = None
        if session_data:
            from app.models.schemas import InterviewSession
            session = InterviewSession(
                id=session_data["id"],
                analysis_id=analysis_id,
                questions=[from_dict for from_dict in session_data["questions"]],
                answers=session_data["answers"],
                current_index=session_data["current_index"],
                is_completed=session_data["is_completed"],
                average_interview_score=session_data["average_score"]
            )
        
        report_obj = generate_final_preparation_report(analysis_id, resume, jd, match_res, session)
        report = report_obj.model_dump()
    
    return report

# =======================================================
# Supabase Cloud Database Endpoints
# =======================================================

@app.get("/api/supabase/status")
async def get_supabase_status():
    """Returns connectivity and table readiness for Supabase."""
    return check_supabase_conn()

@app.get("/api/supabase/schema")
async def get_supabase_schema():
    """Returns the SQL schema required for Supabase table initialization."""
    schema_path = BASE_DIR / "supabase_schema.sql"
    if schema_path.exists():
        return {"status": "success", "schema_sql": schema_path.read_text(encoding="utf-8")}
    return {"status": "error", "message": "Schema file not found"}

@app.get("/api/supabase/employee-data")
async def get_employee_data(limit: int = 50):
    """Fetches employee / candidate records stored in Supabase."""
    return {"status": "success", "records": get_supabase_employee_data(limit)}

@app.get("/api/supabase/questions")
async def get_questions(analysis_id: Optional[str] = None, limit: int = 100):
    """Fetches interview questions stored in Supabase."""
    return {"status": "success", "records": get_supabase_questions(analysis_id, limit)}

@app.get("/api/supabase/performance")
async def get_performance_details(analysis_id: Optional[str] = None, limit: int = 50):
    """Fetches candidate performance details stored in Supabase."""
    return {"status": "success", "records": get_supabase_performance(analysis_id, limit)}

@app.post("/api/supabase/sync-all")
async def sync_all_to_supabase():
    """Syncs all historical records from local SQLite to Supabase."""
    result = sync_all_from_sqlite_to_supabase()
    return result

# =======================================================
# Static File & UI Delivery
# =======================================================

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def root():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return JSONResponse(
        content={"message": "ResumeMatch AI backend is active. Frontend static files are loading."},
        status_code=200
    )
