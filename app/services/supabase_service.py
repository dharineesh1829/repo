"""
Supabase Database Service for ResumeMatch AI.
Provides cloud persistence for:
1. Employee & Candidate Data ('employee_data')
2. Interview Questions ('questions')
3. Candidate Performance Details ('performance_details')
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.config import SUPABASE_URL, SUPABASE_KEY, is_supabase_available

logger = logging.getLogger("supabase_service")

# Initialize client lazily or at import
_supabase_client = None

def get_supabase_client():
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    
    if not is_supabase_available():
        return None
    
    try:
        from supabase import create_client, Client
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return _supabase_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        return None

def check_connection() -> Dict[str, Any]:
    """Tests connection to Supabase and reports status of required tables."""
    if not is_supabase_available():
        return {
            "configured": False,
            "connected": False,
            "url": SUPABASE_URL or "Not set",
            "message": "Supabase credentials are not configured in .env",
            "tables": {}
        }
    
    client = get_supabase_client()
    if not client:
        return {
            "configured": True,
            "connected": False,
            "url": SUPABASE_URL,
            "message": "Failed to create Supabase client instance.",
            "tables": {}
        }
    
    tables_status = {}
    target_tables = ["employee_data", "questions", "performance_details"]
    
    for table_name in target_tables:
        try:
            res = client.table(table_name).select("*").limit(1).execute()
            tables_status[table_name] = {
                "exists": True,
                "count": len(res.data) if res.data is not None else 0,
                "status": "Ready"
            }
        except Exception as e:
            err_msg = str(e)
            if "PGRST205" in err_msg or "Could not find the table" in err_msg or "404" in err_msg:
                tables_status[table_name] = {
                    "exists": False,
                    "status": "Table does not exist. Run supabase_schema.sql in Supabase SQL Editor.",
                    "error": "Table missing"
                }
            else:
                tables_status[table_name] = {
                    "exists": False,
                    "status": f"Access error: {err_msg}",
                    "error": err_msg
                }
    
    all_exist = all(t.get("exists", False) for t in tables_status.values())
    
    return {
        "configured": True,
        "connected": True,
        "url": SUPABASE_URL,
        "all_tables_ready": all_exist,
        "tables": tables_status,
        "message": "Connected to Supabase successfully" if all_exist else "Connected to Supabase, but some tables need to be created using supabase_schema.sql"
    }

# =========================================================================
# 1. EMPLOYEE & CANDIDATE DATA ("EMPLOY DTAT")
# =========================================================================

def save_employee_to_supabase(
    analysis_id: str,
    title: str = "Resume Analysis",
    resume_raw: str = "",
    resume_filename: str = "",
    resume_parsed: Optional[Dict[str, Any]] = None,
    jd_raw: str = "",
    jd_filename: str = "",
    jd_parsed: Optional[Dict[str, Any]] = None
) -> bool:
    """Saves or updates employee/candidate record in Supabase 'employee_data' table."""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        cand_name = "Candidate"
        email = ""
        phone = ""
        job_title = "Target Position"

        if resume_parsed:
            cand_name = resume_parsed.get("candidate_name") or cand_name
            email = resume_parsed.get("email") or ""
            phone = resume_parsed.get("phone") or ""
        
        if jd_parsed:
            job_title = jd_parsed.get("job_title") or job_title

        now_iso = datetime.utcnow().isoformat()
        
        payload = {
            "id": analysis_id,
            "candidate_name": cand_name,
            "email": email,
            "phone": phone,
            "title": title,
            "resume_filename": resume_filename or "",
            "resume_raw": resume_raw or "",
            "resume_parsed": resume_parsed or {},
            "job_title": job_title,
            "jd_filename": jd_filename or "",
            "jd_raw": jd_raw or "",
            "jd_parsed": jd_parsed or {},
            "updated_at": now_iso
        }

        client.table("employee_data").upsert(payload).execute()
        logger.info(f"Synced employee data for {analysis_id} ({cand_name}) to Supabase.")
        return True
    except Exception as e:
        logger.warning(f"Could not sync employee data to Supabase: {e}")
        return False

# =========================================================================
# 2. QUESTIONS ("QUTION")
# =========================================================================

def save_questions_to_supabase(analysis_id: str, questions: List[Any]) -> bool:
    """Saves interview questions to Supabase 'questions' table."""
    client = get_supabase_client()
    if not client or not questions:
        return False
    
    try:
        rows = []
        now_iso = datetime.utcnow().isoformat()
        
        for idx, q in enumerate(questions):
            q_dict = q if isinstance(q, dict) else q.model_dump()
            rows.append({
                "id": q_dict.get("id") or f"{analysis_id}_q_{idx}",
                "analysis_id": analysis_id,
                "category": q_dict.get("category", "General"),
                "question_text": q_dict.get("question_text", ""),
                "context_source": q_dict.get("context_source", ""),
                "order_index": q_dict.get("order_index", idx),
                "created_at": now_iso
            })
            
        if rows:
            client.table("questions").upsert(rows).execute()
            logger.info(f"Synced {len(rows)} interview questions for {analysis_id} to Supabase.")
            return True
        return False
    except Exception as e:
        logger.warning(f"Could not sync questions to Supabase: {e}")
        return False

# =========================================================================
# 3. PERFORMANCE DETAILS ("THERE PREFORMANCE DETAIL")
# =========================================================================

def save_performance_to_supabase(
    analysis_id: str,
    candidate_name: str = "",
    job_title: str = "",
    match_result: Optional[Dict[str, Any]] = None,
    interview_session: Optional[Dict[str, Any]] = None,
    preparation_report: Optional[Dict[str, Any]] = None
) -> bool:
    """Saves candidate performance details (scores, evaluations, checklist) to Supabase 'performance_details' table."""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        perf_id = f"perf_{analysis_id}"
        now_iso = datetime.utcnow().isoformat()

        overall_score = 0
        skill_score = 0
        exp_score = 0
        eligibility = "Pending Evaluation"
        matched = []
        missing = []

        if match_result:
            overall_score = match_result.get("overall_score", 0)
            skill_score = match_result.get("skill_match_score", 0)
            exp_score = match_result.get("experience_match_score", 0)
            eligibility = match_result.get("eligibility_status", "Pending Evaluation")
            matched = match_result.get("matched_skills", [])
            missing = match_result.get("missing_skills", [])

        avg_interview_score = 0.0
        answers_dict = {}
        if interview_session:
            avg_interview_score = interview_session.get("average_interview_score") or interview_session.get("average_score") or 0.0
            answers_dict = interview_session.get("answers") or {}

        payload = {
            "id": perf_id,
            "analysis_id": analysis_id,
            "candidate_name": candidate_name or "Candidate",
            "job_title": job_title or "Target Position",
            "overall_match_score": overall_score,
            "skill_match_score": skill_score,
            "experience_match_score": exp_score,
            "eligibility_status": eligibility,
            "matched_skills": matched,
            "missing_skills": missing,
            "average_interview_score": avg_interview_score,
            "answers_evaluations": answers_dict,
            "preparation_report": preparation_report or {},
            "updated_at": now_iso
        }

        client.table("performance_details").upsert(payload).execute()
        logger.info(f"Synced performance details for {analysis_id} to Supabase.")
        return True
    except Exception as e:
        logger.warning(f"Could not sync performance details to Supabase: {e}")
        return False

# =========================================================================
# Query Helpers for Frontend Views
# =========================================================================

def get_supabase_employee_data(limit: int = 50) -> List[Dict[str, Any]]:
    client = get_supabase_client()
    if not client:
        return []
    try:
        res = client.table("employee_data").select("*").order("created_at", desc=True).limit(limit).execute()
        return res.data or []
    except Exception as e:
        logger.warning(f"Error fetching employee data from Supabase: {e}")
        return []

def get_supabase_questions(analysis_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    client = get_supabase_client()
    if not client:
        return []
    try:
        query = client.table("questions").select("*")
        if analysis_id:
            query = query.eq("analysis_id", analysis_id)
        res = query.order("order_index", desc=False).limit(limit).execute()
        return res.data or []
    except Exception as e:
        logger.warning(f"Error fetching questions from Supabase: {e}")
        return []

def get_supabase_performance(analysis_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    client = get_supabase_client()
    if not client:
        return []
    try:
        query = client.table("performance_details").select("*")
        if analysis_id:
            query = query.eq("analysis_id", analysis_id)
        res = query.order("updated_at", desc=True).limit(limit).execute()
        return res.data or []
    except Exception as e:
        logger.warning(f"Error fetching performance details from Supabase: {e}")
        return []

def sync_all_from_sqlite_to_supabase() -> Dict[str, Any]:
    """Syncs all analyses, questions, and performance records from SQLite into Supabase."""
    from app.database import list_analyses, get_analysis, get_interview_session_by_analysis, get_preparation_report
    analyses = list_analyses()
    employee_count = 0
    question_count = 0
    perf_count = 0

    for item in analyses:
        a_id = item["id"]
        full_a = get_analysis(a_id)
        if not full_a:
            continue
        
        ok_emp = save_employee_to_supabase(
            analysis_id=a_id,
            title=full_a.get("title", ""),
            resume_raw=full_a.get("resume_raw", ""),
            resume_filename=full_a.get("resume_filename", ""),
            resume_parsed=full_a.get("resume_parsed"),
            jd_raw=full_a.get("jd_raw", ""),
            jd_filename=full_a.get("jd_filename", ""),
            jd_parsed=full_a.get("jd_parsed")
        )
        if ok_emp:
            employee_count += 1
        
        sess = get_interview_session_by_analysis(a_id)
        if sess and sess.get("questions"):
            ok_q = save_questions_to_supabase(a_id, sess["questions"])
            if ok_q:
                question_count += len(sess["questions"])
        
        cand_name = (full_a.get("resume_parsed") or {}).get("candidate_name") or full_a.get("title", "Candidate")
        job_title = (full_a.get("jd_parsed") or {}).get("job_title", "Position")
        match_res = full_a.get("match_result")
        prep_rep = get_preparation_report(a_id)
        
        ok_perf = save_performance_to_supabase(
            analysis_id=a_id,
            candidate_name=cand_name,
            job_title=job_title,
            match_result=match_res,
            interview_session=sess,
            preparation_report=prep_rep
        )
        if ok_perf:
            perf_count += 1

    return {
        "status": "success",
        "synced_employees": employee_count,
        "synced_questions": question_count,
        "synced_performance_records": perf_count,
        "total_local_analyses": len(analyses)
    }
