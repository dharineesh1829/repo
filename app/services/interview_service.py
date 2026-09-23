"""
Interview Orchestrator and Final Preparation Report Generator.
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.models.schemas import (
    InterviewSession, InterviewQuestion, InterviewAnswer,
    AnswerEvaluation, FinalPreparationReport, PreparationChecklistItem,
    ResumeInformation, JobRequirements, MatchResult
)
from app.services.ai_service import generate_mock_interview_questions, evaluate_answer
import app.database as db

async def start_or_get_interview_session(analysis_id: str, resume: ResumeInformation, jd: JobRequirements) -> InterviewSession:
    """Creates a new interview session or retrieves an existing active one."""
    existing = db.get_interview_session_by_analysis(analysis_id)
    if existing and existing.get("questions"):
        # Reconstruct session
        q_objs = [InterviewQuestion(**q) for q in existing["questions"]]
        a_objs = {k: InterviewAnswer(**v) for k, v in existing.get("answers", {}).items()}
        return InterviewSession(
            id=existing["id"],
            analysis_id=analysis_id,
            questions=q_objs,
            answers=a_objs,
            current_index=existing.get("current_index", 0),
            is_completed=bool(existing.get("is_completed", False)),
            average_interview_score=float(existing.get("average_score", 0.0))
        )

    # Generate tailored questions
    questions = generate_mock_interview_questions(resume, jd)
    session_id = str(uuid.uuid4())
    session = InterviewSession(
        id=session_id,
        analysis_id=analysis_id,
        questions=questions,
        answers={},
        current_index=0,
        is_completed=False,
        average_interview_score=0.0
    )

    db.save_interview_session(session.model_dump())
    try:
        from app.services.supabase_service import save_questions_to_supabase
        save_questions_to_supabase(analysis_id, session.questions)
    except Exception:
        pass
    return session

async def submit_candidate_answer(
    session_id: str,
    question_id: str,
    answer_text: str,
    time_spent_seconds: int = 0
) -> Dict[str, Any]:
    """Evaluates the submitted answer and persists it to the database."""
    session_data = db.get_interview_session(session_id)
    if not session_data:
        raise ValueError(f"Interview session '{session_id}' not found.")

    questions = [InterviewQuestion(**q) for q in session_data["questions"]]
    target_q = next((q for q in questions if q.id == question_id), None)
    if not target_q:
        raise ValueError(f"Question '{question_id}' not found in this interview session.")

    # Evaluate using AI/NLP
    evaluation: AnswerEvaluation = await evaluate_answer(target_q, answer_text)

    # Record answer
    answers = session_data.get("answers", {})
    answer_obj = InterviewAnswer(
        question_id=question_id,
        question_category=target_q.category,
        question_text=target_q.question_text,
        user_answer=answer_text,
        time_spent_seconds=time_spent_seconds,
        evaluation=evaluation
    )
    answers[question_id] = answer_obj.model_dump()

    # Recalculate average interview score
    scores = [a["evaluation"]["overall_score"] for a in answers.values() if a.get("evaluation")]
    avg_score = round(sum(scores) / max(1, len(scores)), 1) if scores else 0.0

    # Advance current index
    curr_idx = session_data.get("current_index", 0)
    is_completed = len(answers) >= len(questions)

    session_data["answers"] = answers
    session_data["average_interview_score"] = avg_score
    session_data["current_index"] = min(len(questions) - 1, curr_idx + 1)
    session_data["is_completed"] = is_completed

    db.save_interview_session(session_data)

    try:
        from app.services.supabase_service import save_performance_to_supabase
        analysis = db.get_analysis(session_data.get("analysis_id", ""))
        cand_name = (analysis.get("resume_parsed") or {}).get("candidate_name") or "Candidate" if analysis else "Candidate"
        job_title = (analysis.get("jd_parsed") or {}).get("job_title") or "Position" if analysis else "Position"
        match_result = analysis.get("match_result") if analysis else None
        prep_report = db.get_preparation_report(session_data.get("analysis_id", ""))
        save_performance_to_supabase(
            analysis_id=session_data.get("analysis_id"),
            candidate_name=cand_name,
            job_title=job_title,
            match_result=match_result,
            interview_session=session_data,
            preparation_report=prep_report
        )
    except Exception:
        pass

    return {
        "evaluation": evaluation.model_dump(),
        "average_score": avg_score,
        "is_completed": is_completed,
        "answered_count": len(answers),
        "total_questions": len(questions)
    }

def generate_final_preparation_report(
    analysis_id: str,
    resume: ResumeInformation,
    jd: JobRequirements,
    match_result: MatchResult,
    session: Optional[InterviewSession]
) -> FinalPreparationReport:
    """Assembles the comprehensive Final Preparation Report & Action Checklist."""
    cand_name = resume.candidate_name or "Candidate"
    
    interview_avg = session.average_interview_score if session else 0.0
    answers = session.answers if session else {}
    
    interview_strengths = []
    interview_weaknesses = []
    questions_needing_prep = []

    for q_id, ans in answers.items():
        eval_data = ans.evaluation
        if eval_data:
            if eval_data.overall_score >= 8:
                interview_strengths.extend(eval_data.what_you_did_well)
            else:
                interview_weaknesses.extend(eval_data.what_you_can_improve)
                questions_needing_prep.append({
                    "category": ans.question_category,
                    "question": ans.question_text,
                    "score": eval_data.overall_score,
                    "better_answer": eval_data.better_answer_approach,
                    "missing_points": eval_data.missing_points
                })

    if not interview_strengths:
        interview_strengths = [
            "Clear technical communication on foundational concepts.",
            "Relevant real-world project anecdotes referenced in answers."
        ]
    if not interview_weaknesses:
        interview_weaknesses = [
            "Elaborate on production scalability constraints and metrics.",
            "Adopt the structured STAR framework for behavioral responses."
        ]

    # Deduplicate strengths & weaknesses
    interview_strengths = list(dict.fromkeys(interview_strengths))[:4]
    interview_weaknesses = list(dict.fromkeys(interview_weaknesses))[:4]

    # Recommended Topics
    recommended_topics = []
    for m in match_result.missing_skills:
        recommended_topics.append(f"{m} Core Architecture & Best Practices")
    recommended_topics.extend([
        "STAR Storytelling for Behavioral & Leadership Prompts",
        "System Architecture & API Scalability Trade-offs",
        "Query Optimization & Database Indexing Fundamentals"
    ])
    recommended_topics = list(dict.fromkeys(recommended_topics))[:5]

    # Final Preparation Checklist
    checklist = [
        PreparationChecklistItem(
            id="chk-1",
            title="Review Missing Skills Fundamentals",
            category="Technical",
            completed=False,
            description=f"Spend 2 hours reviewing foundational syntax and concepts for {', '.join(match_result.missing_skills[:2]) if match_result.missing_skills else 'cloud deployments'}."
        ),
        PreparationChecklistItem(
            id="chk-2",
            title="Polish STAR Behavioral Stories",
            category="Behavioral",
            completed=False,
            description="Prepare 3 concise 90-second stories detailing a technical challenge, a conflict/deadline, and an innovative deliverable."
        ),
        PreparationChecklistItem(
            id="chk-3",
            title="Deep-Dive Into Resume Projects",
            category="Resume",
            completed=False,
            description=f"Be ready to sketch the system diagram and defend architecture choices for {resume.projects[0].name if resume.projects else 'your primary project'}."
        ),
        PreparationChecklistItem(
            id="chk-4",
            title="Prepare Reverse-Interview Questions",
            category="Company",
            completed=False,
            description=f"Prepare 3 strategic questions for {jd.company} regarding their engineering roadmaps, CI/CD pipeline, and team mentorship."
        ),
        PreparationChecklistItem(
            id="chk-5",
            title="Practice Live Coding / SQL Queries",
            category="Technical",
            completed=False,
            description="Solve 2 intermediate SQL problems focusing on JOINs, GROUP BY aggregations, and window functions."
        )
    ]

    report = FinalPreparationReport(
        analysis_id=analysis_id,
        candidate_name=cand_name,
        job_title=jd.job_title,
        overall_match_score=match_result.overall_score,
        eligibility_status=match_result.eligibility_status,
        interview_average_score=interview_avg,
        top_strengths=match_result.strengths,
        skill_gaps=match_result.missing_skills,
        recommended_skills=[s.name for s in match_result.recommended_skills],
        interview_strengths=interview_strengths,
        interview_weaknesses=interview_weaknesses,
        questions_needing_prep=questions_needing_prep,
        recommended_topics=recommended_topics,
        checklist=checklist,
        generated_at=datetime.now().strftime("%B %d, %Y - %I:%M %p")
    )

    db.save_preparation_report(analysis_id, report.model_dump())
    try:
        from app.services.supabase_service import save_performance_to_supabase
        save_performance_to_supabase(
            analysis_id=analysis_id,
            candidate_name=cand_name,
            job_title=jd.job_title,
            match_result=match_result.model_dump(),
            interview_session=session.model_dump() if session else None,
            preparation_report=report.model_dump()
        )
    except Exception:
        pass
    return report
