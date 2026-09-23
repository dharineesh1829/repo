"""
Automated unit and integration test suite for ResumeMatch AI.
"""
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.services.document_parser import extract_document_text, DocumentParsingError
from app.services.ai_service import parse_resume_nlp, parse_jd_nlp, generate_mock_interview_questions, evaluate_interview_answer_nlp
from app.services.matching_engine import compare_resume_to_jd
from app.models.schemas import ResumeInformation, JobRequirements
from fastapi.testclient import TestClient
from app.main import app

def test_document_parser():
    print("Testing document parser...")
    sample_txt_path = root_dir / "demo_files" / "sample_resume.txt"
    txt_bytes = sample_txt_path.read_bytes()
    text, ftype = extract_document_text("sample_resume.txt", txt_bytes)
    assert len(text) > 200, "Failed to extract text from TXT"
    assert ftype == "TXT"
    assert "Alex Chen" in text or "ALEX CHEN" in text

    sample_docx_path = root_dir / "demo_files" / "sample_resume.docx"
    docx_bytes = sample_docx_path.read_bytes()
    text_docx, ftype_docx = extract_document_text("sample_resume.docx", docx_bytes)
    assert len(text_docx) > 200, "Failed to extract text from DOCX"
    assert ftype_docx == "DOCX"
    print("✓ Document parser passed.")

def test_nlp_extraction_and_matching():
    print("Testing NLP extraction and 5-pillar matching engine...")
    resume_text = (root_dir / "demo_files" / "sample_resume.txt").read_text(encoding="utf-8")
    jd_text = (root_dir / "demo_files" / "sample_job_description.txt").read_text(encoding="utf-8")

    resume_info = parse_resume_nlp(resume_text)
    assert "Python" in resume_info.skills or "Python" in resume_info.tools_and_technologies
    assert "Machine Learning" in resume_info.skills or "Machine Learning" in resume_info.tools_and_technologies
    assert len(resume_info.projects) >= 2

    jd_info = parse_jd_nlp(jd_text)
    assert len(jd_info.required_skills) >= 4

    match_result = compare_resume_to_jd(resume_info, jd_info)
    assert 0 <= match_result.overall_score <= 100
    assert 0 <= match_result.skill_match_score <= 100
    assert 0 <= match_result.experience_match_score <= 100
    assert match_result.eligibility_status in ["Eligible", "Partially Eligible", "Not Eligible"]
    assert len(match_result.matched_skills) > 0
    assert len(match_result.missing_skills) > 0
    print(f"✓ Matching engine passed. Overall score: {match_result.overall_score}%, Status: {match_result.eligibility_status}")

def test_mock_interview_and_eval():
    print("Testing mock interview question generator & answer evaluation...")
    resume_text = (root_dir / "demo_files" / "sample_resume.txt").read_text(encoding="utf-8")
    jd_text = (root_dir / "demo_files" / "sample_job_description.txt").read_text(encoding="utf-8")
    resume_info = parse_resume_nlp(resume_text)
    jd_info = parse_jd_nlp(jd_text)

    questions = generate_mock_interview_questions(resume_info, jd_info)
    categories = {q.category for q in questions}
    assert "HR" in categories
    assert "Technical" in categories
    assert "Behavioral" in categories
    assert "Resume-Based" in categories
    assert "JD-Specific" in categories
    assert len(questions) >= 5

    test_q = questions[1]
    sample_answer = "To prevent overfitting in Python with machine learning models, I apply L1/L2 regularization, dropout in neural networks, and evaluate with 5-fold cross-validation. For unbalanced datasets, precision, recall, and F1-score are much more informative than accuracy."
    evaluation = evaluate_interview_answer_nlp(test_q, sample_answer)
    assert 0 <= evaluation.technical_accuracy_score <= 10
    assert 0 <= evaluation.overall_score <= 10
    assert len(evaluation.what_you_did_well) > 0
    assert len(evaluation.better_answer_approach) > 10
    print(f"✓ Interview & evaluation passed. Evaluated score: {evaluation.overall_score}/10")

def test_fastapi_endpoints():
    print("Testing FastAPI endpoints via TestClient...")
    client = TestClient(app)

    # Health
    r_health = client.get("/api/health")
    assert r_health.status_code == 200
    assert r_health.json()["status"] == "online"

    # Demo Load
    r_demo = client.post("/api/demo/load")
    assert r_demo.status_code == 200
    demo_data = r_demo.json()
    assert demo_data["status"] == "success"
    analysis_id = demo_data["analysis_id"]
    assert len(analysis_id) > 10

    # Get Analysis
    r_analysis = client.get(f"/api/analysis/{analysis_id}")
    assert r_analysis.status_code == 200
    assert r_analysis.json()["id"] == analysis_id

    # Interview Session
    r_interview = client.get(f"/api/interview/{analysis_id}")
    assert r_interview.status_code == 200
    interview_data = r_interview.json()
    session_id = interview_data["id"]
    first_q_id = interview_data["questions"][0]["id"]

    # Submit Answer
    r_sub = client.post("/api/interview/submit", json={
        "session_id": session_id,
        "question_id": first_q_id,
        "answer_text": "I am passionate about building scalable ML services and collaborating with engineers to make an impact.",
        "time_spent_seconds": 45
    })
    assert r_sub.status_code == 200
    assert r_sub.json()["status"] == "success"

    # Preparation Report
    r_prep = client.get(f"/api/interview/{analysis_id}/report")
    assert r_prep.status_code == 200
    report_data = r_prep.json()
    assert report_data["candidate_name"] != ""
    assert len(report_data["checklist"]) > 0

    # Supabase Endpoints
    r_sb_status = client.get("/api/supabase/status")
    assert r_sb_status.status_code == 200
    assert r_sb_status.json()["configured"] is True

    r_sb_schema = client.get("/api/supabase/schema")
    assert r_sb_schema.status_code == 200
    assert "public.employee_data" in r_sb_schema.json()["schema_sql"]

    r_sb_sync = client.post("/api/supabase/sync-all")
    assert r_sb_sync.status_code == 200

    print("✓ All FastAPI API and Supabase integration tests passed successfully.")


if __name__ == "__main__":
    test_document_parser()
    test_nlp_extraction_and_matching()
    test_mock_interview_and_eval()
    test_fastapi_endpoints()
    print("\n🎉 ALL UNIT & INTEGRATION TESTS PASSED! 🎉")
