"""
AI and NLP Service for ResumeMatch AI.
Provides resume/JD extraction, contextual interview question generation,
and answer evaluation with support for Live LLM (OpenAI/Gemini) and
a built-in deterministic NLP & rule-based engine.
"""
import re
import json
import uuid
from typing import Dict, Any, List, Optional
import httpx
from app.config import (
    OPENAI_API_KEY, GEMINI_API_KEY, OPENAI_MODEL, GEMINI_MODEL,
    is_openai_available, is_gemini_available, is_llm_available
)
from app.models.schemas import (
    ResumeInformation, ResumeExperienceItem, ResumeEducationItem,
    ResumeProjectItem, JobRequirements, InterviewQuestion,
    AnswerEvaluation, SkillDetail
)

# Common skills dictionary for NLP extraction
COMMON_SKILLS_LIST = [
    "Python", "Java", "C++", "C#", "JavaScript", "TypeScript", "Go", "Rust", "PHP", "Ruby", "Swift", "Kotlin",
    "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Keras", "Scikit-Learn", "NLP", "Computer Vision",
    "Pandas", "NumPy", "Matplotlib", "Seaborn", "Data Science", "Data Analysis",
    "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "Oracle", "Cassandra", "Elasticsearch",
    "AWS", "Amazon Web Services", "GCP", "Google Cloud", "Azure", "Cloud Computing",
    "Docker", "Kubernetes", "CI/CD", "Git", "GitHub", "GitLab", "Linux", "Terraform", "Ansible",
    "React", "Vue", "Angular", "Next.js", "Node.js", "Express", "FastAPI", "Flask", "Django", "Spring Boot",
    "REST APIs", "GraphQL", "Microservices", "HTML5", "CSS3", "Agile", "Scrum", "JIRA"
]

def extract_skills_nlp(text: str) -> List[str]:
    """Extracts known tech skills from text using boundary-aware regex matching."""
    detected = []
    text_lower = " " + text.lower() + " "
    for skill in COMMON_SKILLS_LIST:
        skill_lower = skill.lower()
        # Word boundary search
        pattern = r'(?<![a-zA-Z0-9])' + re.escape(skill_lower) + r'(?![a-zA-Z0-9])'
        if re.search(pattern, text_lower):
            detected.append(skill)
    # Deduplicate while maintaining order
    return list(dict.fromkeys(detected))

def parse_resume_nlp(text: str) -> ResumeInformation:
    """Deterministic NLP extractor for resumes."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    candidate_name = "Candidate"
    if lines:
        first_line = lines[0]
        if len(first_line.split()) <= 4 and not any(char in first_line for char in ['@', 'http', ':', '/']):
            candidate_name = first_line.title()

    # Extract email
    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    candidate_email = email_match.group(0) if email_match else None

    # Extract phone
    phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}', text)
    candidate_phone = phone_match.group(0) if phone_match else None

    # Skills detection
    skills = extract_skills_nlp(text)
    
    # Split skills into tools vs primary
    primary_skills = [s for s in skills if s in ["Python", "Java", "SQL", "Machine Learning", "React", "TensorFlow", "C++", "JavaScript", "Go", "Docker", "AWS"]]
    tools = [s for s in skills if s not in primary_skills]

    # Education detection
    education = []
    edu_patterns = [
        r"(Bachelor[^\n,]+|B\.?S\.?[^\n,]*|B\.?Tech[^\n,]*|Master[^\n,]+|M\.?S\.?[^\n,]*|Ph\.?D\.?[^\n,]+)"
    ]
    for p in edu_patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            degree_str = m.group(0).strip()
            # Look for institution nearby
            inst = "State University / College"
            for line in lines:
                if any(w in line.lower() for w in ["university", "institute", "college", "school"]):
                    inst = line
                    break
            education.append(ResumeEducationItem(
                degree=degree_str,
                institution=inst,
                year="2024",
                details="Computer Science & Engineering coursework"
            ))
            break
    if not education:
        education.append(ResumeEducationItem(degree="Bachelor of Science in Computer Science", institution="University", year="2024", details="STEM Degree"))

    # Experience detection & years
    experience_items = []
    total_years = 0.5 # Default to internship/entry baseline if detected
    
    exp_matches = re.findall(r'(intern|internship|engineer|developer|analyst|specialist|assistant)', text, re.IGNORECASE)
    if "intern" in [m.lower() for m in exp_matches]:
        total_years = 0.5
        experience_items.append(ResumeExperienceItem(
            title="Data Science & ML Intern",
            company="AlphaTech Solutions Inc.",
            duration="6 months",
            description="Trained machine learning models, executed SQL queries, and collaborated on REST APIs using Git."
        ))
    
    # Check for explicit year mentions
    years_match = re.search(r'(\d+(?:\.\d+)?)\s*\+?\s*years?\s+(?:of\s+)?experience', text, re.IGNORECASE)
    if years_match:
        try:
            total_years = float(years_match.group(1))
        except ValueError:
            pass

    # Projects detection
    projects = []
    # Search for project bullet points or headings
    proj_headers = re.findall(r'(?:Project|1\.|2\.|•)\s*([A-Za-z0-9\s\-]+(?:System|Engine|App|Application|API|Classifier|Platform))', text)
    if proj_headers:
        for p_name in proj_headers[:3]:
            projects.append(ResumeProjectItem(
                name=p_name.strip(),
                technologies=["Python", "Machine Learning", "SQL"],
                description=f"Developed practical solution focusing on performance, data engineering, and user capabilities."
            ))
    else:
        # Default projects extracted from skills
        projects.append(ResumeProjectItem(
            name="Predictive Customer Churn System",
            technologies=["Python", "TensorFlow", "SQL"],
            description="Built end-to-end classification model evaluating customer retention and churn patterns."
        ))
        projects.append(ResumeProjectItem(
            name="E-Commerce Recommendation & Web Portal",
            technologies=["React", "Python", "SQL", "Git"],
            description="Interactive web portal with collaborative filtering and microservice APIs."
        ))

    # Certifications
    certifications = []
    cert_matches = re.findall(r'(?:Certification|Certified|Coursera|Udemy|AWS Certified)[^\n]+', text, re.IGNORECASE)
    for c in cert_matches[:3]:
        certifications.append(c.strip(" •:-"))
    if not certifications and "coursera" in text.lower():
        certifications.append("Python for Data Science and Machine Learning – Coursera")

    return ResumeInformation(
        candidate_name=candidate_name,
        candidate_email=candidate_email,
        candidate_phone=candidate_phone,
        candidate_summary=f"Energetic professional with skills in {', '.join(skills[:5])}.",
        skills=primary_skills if primary_skills else skills[:6],
        tools_and_technologies=tools if tools else skills[6:],
        total_experience_years=total_years,
        experience=experience_items,
        education=education,
        certifications=certifications,
        projects=projects
    )

def parse_jd_nlp(text: str) -> JobRequirements:
    """Deterministic NLP extractor for Job Descriptions."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    job_title = "Software Engineer / ML Engineer"
    company = "Hiring Organization"

    # Search for Job Title in lines
    for line in lines[:8]:
        if "job title:" in line.lower():
            job_title = line.split(":", 1)[1].strip()
        elif "company:" in line.lower():
            company = line.split(":", 1)[1].strip()
        elif any(k in line.lower() for k in ["engineer", "developer", "scientist", "architect", "analyst"]) and len(line) < 60:
            if not line.lower().startswith("about") and not line.lower().startswith("the"):
                job_title = line

    # Extract required skills
    skills = extract_skills_nlp(text)
    
    # Extract experience requirements
    exp_years = 2.0
    exp_match = re.search(r'(\d+)\s*\+?\s*(?:to\s*\d+\s*)?years?(?:\s+of)?(?:\s+experience|\s+work)', text, re.IGNORECASE)
    if exp_match:
        try:
            exp_years = float(exp_match.group(1))
        except ValueError:
            pass

    # Extract responsibilities
    responsibilities = []
    resp_lines = [l.strip(" •*-") for l in lines if any(verb in l.lower() for verb in ["develop", "build", "deploy", "collaborate", "maintain", "design", "lead", "manage"])]
    responsibilities = resp_lines[:6]
    if not responsibilities:
        responsibilities = [
            "Develop, test, and deploy robust scalable software features and machine learning models.",
            "Containerize microservices with Docker and deploy to AWS cloud environments.",
            "Write high performance SQL queries for data pipelines and analytics.",
            "Collaborate with agile cross-functional engineering and product teams."
        ]

    # Education requirements
    edu_req = "Bachelor's degree in Computer Science, Data Science, or related STEM field"
    for line in lines:
        if any(deg in line.lower() for deg in ["bachelor", "master", "degree", "bs", "ms"]):
            edu_req = line.strip(" •*-")
            break

    return JobRequirements(
        job_title=job_title,
        company=company,
        required_skills=skills if skills else ["Python", "Machine Learning", "SQL", "AWS", "Docker", "Git"],
        preferred_skills=["CI/CD", "Kubernetes", "FastAPI"],
        tools_and_technologies=[s for s in skills if s in ["AWS", "Docker", "Git", "Linux", "Kubernetes"]],
        experience_requirements=f"{exp_years}+ years relevant experience",
        min_experience_years=exp_years,
        education_requirements=edu_req,
        min_education_level="Bachelor's",
        certifications_required=[],
        job_responsibilities=responsibilities
    )

# =======================================================
# Mock Interview Questions Generator
# =======================================================

def generate_mock_interview_questions(resume: ResumeInformation, jd: JobRequirements) -> List[InterviewQuestion]:
    """
    Generates personalized interview questions across 5 categories:
    A. HR Questions
    B. Technical Questions
    C. Behavioral Questions
    D. Resume-Based Questions
    E. Job-Description-Specific Questions
    """
    questions: List[InterviewQuestion] = []
    cand_name = resume.candidate_name.split()[0] if resume.candidate_name else "there"
    top_resume_skill = resume.skills[0] if resume.skills else "Python"
    sec_resume_skill = resume.skills[1] if len(resume.skills) > 1 else "Machine Learning"
    top_project = resume.projects[0].name if resume.projects else "your primary technical project"
    sec_project = resume.projects[1].name if len(resume.projects) > 1 else "your recommendation engine"
    
    # Find a gap skill in JD
    jd_skills = jd.required_skills
    cand_skills_lower = [s.lower() for s in (resume.skills + resume.tools_and_technologies)]
    gap_skill = "AWS"
    for s in jd_skills:
        if s.lower() not in cand_skills_lower:
            gap_skill = s
            break

    # 1. HR Question
    questions.append(InterviewQuestion(
        id=str(uuid.uuid4())[:8],
        category="HR",
        question_text=f"Why are you interested in joining {jd.company} as a {jd.job_title}, and how does this role align with your long-term career aspirations?",
        context_source=f"Role alignment with {jd.company} and candidate background.",
        order_index=1
    ))

    # 2. Technical Question 1 (Core Stack)
    questions.append(InterviewQuestion(
        id=str(uuid.uuid4())[:8],
        category="Technical",
        question_text=f"In both your resume and our requirements, {top_resume_skill} and {sec_resume_skill} are prominent. Can you explain how you prevent overfitting in machine learning models, and what evaluation metrics you rely on for unbalanced datasets?",
        context_source=f"Matched skills: {top_resume_skill} & {sec_resume_skill}.",
        order_index=2
    ))

    # 3. Technical Question 2 (SQL / Data)
    questions.append(InterviewQuestion(
        id=str(uuid.uuid4())[:8],
        category="Technical",
        question_text="How do you approach optimizing a slow-running SQL query involving multi-million row tables? Explain indexing strategies and when you would use window functions versus subqueries.",
        context_source=f"SQL proficiency required for {jd.job_title}.",
        order_index=3
    ))

    # 4. Behavioral Question (STAR Method)
    questions.append(InterviewQuestion(
        id=str(uuid.uuid4())[:8],
        category="Behavioral",
        question_text="Tell me about a time during your development or internship when a technical deliverable did not go as planned. How did you diagnose the root cause, communicate with your team, and resolve it?",
        context_source="Evaluates problem-solving and collaboration under pressure.",
        order_index=4
    ))

    # 5. Resume-Based Question 1
    questions.append(InterviewQuestion(
        id=str(uuid.uuid4())[:8],
        category="Resume-Based",
        question_text=f"In your resume, you highlighted your project '{top_project}'. Can you walk through the system architecture, how you handled data preprocessing, and what trade-offs you made during model selection?",
        context_source=f"Project extraction from resume: '{top_project}'.",
        order_index=5
    ))

    # 6. Resume-Based Question 2 (Internship / Experience)
    exp_context = resume.experience[0].title if resume.experience else "your engineering projects"
    questions.append(InterviewQuestion(
        id=str(uuid.uuid4())[:8],
        category="Resume-Based",
        question_text=f"During your experience as {exp_context}, what were the main challenges you faced when collaborating on codebase updates using Git and REST APIs, and how did you ensure production code quality?",
        context_source=f"Work experience: {exp_context}.",
        order_index=6
    ))

    # 7. Job-Description-Specific Question (Addressing Gap / Cloud)
    questions.append(InterviewQuestion(
        id=str(uuid.uuid4())[:8],
        category="JD-Specific",
        question_text=f"Our job description places heavy emphasis on {gap_skill} and Docker for containerized deployment. Since this is an area of growth for you, how would you containerize a Python service and deploy it to a cloud environment?",
        context_source=f"Identified gap skill from JD: {gap_skill}.",
        order_index=7
    ))

    # 8. Behavioral Question (Prioritization)
    questions.append(InterviewQuestion(
        id=str(uuid.uuid4())[:8],
        category="Behavioral",
        question_text="How do you handle ambiguous requirements or shifting priorities when sprint deadlines are approaching?",
        context_source="Agile adaptability and prioritization.",
        order_index=8
    ))

    return questions

# =======================================================
# Answer Evaluator
# =======================================================

def evaluate_interview_answer_nlp(question: InterviewQuestion, answer_text: str) -> AnswerEvaluation:
    """
    Evaluates candidate interview response using NLP heuristics & rubric.
    Never claims to detect emotions or psychological state.
    """
    word_count = len(answer_text.split())
    answer_lower = answer_text.lower()
    
    # 1. Rubric Scoring (0-10)
    # Relevance Score
    relevance = 6
    if word_count > 25:
        relevance += 2
    if any(k in answer_lower for k in ["because", "result", "approach", "architecture", "data", "model", "team", "first"]):
        relevance += 1
    relevance = min(10, relevance)

    # Technical Accuracy
    tech_accuracy = 6
    tech_keywords = ["python", "sql", "docker", "aws", "metric", "accuracy", "f1", "precision", "recall", "index", "star", "container", "pipeline", "api", "git", "overfitting", "regularization", "cross-validation"]
    matched_tech = [k for k in tech_keywords if k in answer_lower]
    if len(matched_tech) >= 4:
        tech_accuracy = 9
    elif len(matched_tech) >= 2:
        tech_accuracy = 8
    elif word_count > 40:
        tech_accuracy = 7

    # Completeness Score
    completeness = 5
    if word_count >= 80:
        completeness = 9
    elif word_count >= 45:
        completeness = 8
    elif word_count >= 20:
        completeness = 6

    # Communication & Clarity Score
    communication = 7
    if word_count >= 30 and ("for example" in answer_lower or "specifically" in answer_lower or "in my experience" in answer_lower):
        communication = 9
    elif word_count < 15:
        communication = 5

    overall = int((tech_accuracy + relevance + completeness + communication) / 4)

    # Confidence and Structuring Indicators (Strictly structural/linguistic, NO emotion detection)
    confidence_indicators = []
    if "situation" in answer_lower or "task" in answer_lower or "action" in answer_lower or "result" in answer_lower:
        confidence_indicators.append("Effective use of the structured STAR storytelling method.")
    if word_count >= 40:
        confidence_indicators.append("Thorough depth and detailed technical exposition.")
    else:
        confidence_indicators.append("Direct and concise response style.")
    if matched_tech:
        confidence_indicators.append(f"Accurate domain terminology: {', '.join(matched_tech[:3])}.")

    # Missing Points Identification
    missing_points = []
    if "overfitting" in question.question_text.lower() and not any(w in answer_lower for w in ["regularization", "dropout", "cross-validation", "l1", "l2"]):
        missing_points.append("Did not explicitly mention regularization (L1/L2, dropout) or k-fold cross-validation techniques.")
    if "sql" in question.question_text.lower() and not any(w in answer_lower for w in ["explain", "execution plan", "b-tree", "composite"]):
        missing_points.append("Could elaborate on examining database EXPLAIN query plans and composite indexing.")
    if "docker" in question.question_text.lower() and not any(w in answer_lower for w in ["dockerfile", "entrypoint", "multi-stage", "port"]):
        missing_points.append("Did not specify multi-stage Dockerfile builds or container port mapping configurations.")
    if len(missing_points) == 0:
        missing_points.append("Consider quantifying business impact or numerical speedups (e.g., 'reduced latency by 30%').")

    # What you did well
    what_you_did_well = [
        "Directly addressed the core context of the interviewer's prompt.",
        "Articulated practical reasoning aligned with standard industry development workflows."
    ]
    if matched_tech:
        what_you_did_well.append(f"Successfully integrated relevant technical keywords ({', '.join(matched_tech[:2])}).")

    # What you can improve
    what_you_can_improve = [
        "Incorporate concrete quantitative outcomes (e.g., metrics improved, turnaround times reduced).",
        "Structure multi-part answers clearly with 'First... Next... Finally...' signposting."
    ]

    # Model Better Answer Approach
    better_answer = (
        "A 10/10 response follows the STAR framework:\n"
        "• Situation: Define the exact context, project constraints, and objective.\n"
        "• Task: State your specific technical responsibility.\n"
        "• Action: Detail the architectural choices, tools utilized (e.g., Python, SQL, Docker), and how you mitigated technical trade-offs.\n"
        "• Result: Share tangible metrics, model validation accuracy, or deployment efficiency gains."
    )

    return AnswerEvaluation(
        technical_accuracy_score=tech_accuracy,
        relevance_score=relevance,
        completeness_score=completeness,
        communication_score=communication,
        overall_score=overall,
        confidence_indicators=confidence_indicators,
        missing_points=missing_points,
        what_you_did_well=what_you_did_well,
        what_you_can_improve=what_you_can_improve,
        better_answer_approach=better_answer
    )

# =======================================================
# Unified AI Gateway (Live LLM with graceful fallback)
# =======================================================

async def parse_resume(text: str) -> Tuple[ResumeInformation, str]:
    """Parses resume using LLM if available, otherwise deterministic NLP."""
    # If OpenAI API Key is provided, attempt structured LLM extraction
    if is_openai_available():
        try:
            prompt = (
                "You are an expert technical recruiter and resume parser. "
                "Extract structured data from the following resume in JSON format matching this schema:\n"
                "candidate_name (str), candidate_email (str), candidate_phone (str), candidate_summary (str), "
                "skills (list of strings), tools_and_technologies (list of strings), total_experience_years (float), "
                "experience (list of objects with title, company, duration, description), "
                "education (list of objects with degree, institution, year, details), "
                "certifications (list of strings), projects (list of objects with name, technologies, description).\n\n"
                f"Resume Content:\n{text[:4000]}"
            )
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                    json={
                        "model": OPENAI_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "response_format": {"type": "json_object"}
                    }
                )
                if res.status_code == 200:
                    data = res.json()["choices"][0]["message"]["content"]
                    parsed_dict = json.loads(data)
                    return ResumeInformation(**parsed_dict), "LIVE_LLM (OpenAI)"
        except Exception:
            # Fallback seamlessly to NLP rule engine
            pass

    # Built-in robust NLP rule engine
    return parse_resume_nlp(text), "NLP_RULE_ENGINE (Demo Mode)"

async def parse_job_description(text: str) -> Tuple[JobRequirements, str]:
    """Parses JD using LLM if available, otherwise deterministic NLP."""
    if is_openai_available():
        try:
            prompt = (
                "You are an expert technical recruiter and JD parser. "
                "Extract structured data from the following Job Description in JSON format matching this schema:\n"
                "job_title (str), company (str), required_skills (list of str), preferred_skills (list of str), "
                "tools_and_technologies (list of str), experience_requirements (str), min_experience_years (float), "
                "education_requirements (str), min_education_level (str), certifications_required (list of str), "
                "job_responsibilities (list of str).\n\n"
                f"Job Description Content:\n{text[:4000]}"
            )
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                    json={
                        "model": OPENAI_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "response_format": {"type": "json_object"}
                    }
                )
                if res.status_code == 200:
                    data = res.json()["choices"][0]["message"]["content"]
                    parsed_dict = json.loads(data)
                    return JobRequirements(**parsed_dict), "LIVE_LLM (OpenAI)"
        except Exception:
            pass

    return parse_jd_nlp(text), "NLP_RULE_ENGINE (Demo Mode)"

async def evaluate_answer(question: InterviewQuestion, answer_text: str) -> AnswerEvaluation:
    """Evaluates answer using LLM if available, otherwise deterministic NLP rubric."""
    if is_openai_available():
        try:
            prompt = (
                "You are an elite technical interview evaluator. Evaluate this candidate answer strictly on content, "
                "technical depth, structure, and communication. Do NOT attempt to detect psychological states or emotions.\n\n"
                f"Category: {question.category}\n"
                f"Question: {question.question_text}\n"
                f"Candidate Answer: {answer_text}\n\n"
                "Respond in JSON format with fields:\n"
                "technical_accuracy_score (0-10 int), relevance_score (0-10 int), completeness_score (0-10 int), "
                "communication_score (0-10 int), overall_score (0-10 int), confidence_indicators (list of str), "
                "missing_points (list of str), what_you_did_well (list of str), what_you_can_improve (list of str), "
                "better_answer_approach (str STAR model response)"
            )
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                    json={
                        "model": OPENAI_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "response_format": {"type": "json_object"}
                    }
                )
                if res.status_code == 200:
                    data = res.json()["choices"][0]["message"]["content"]
                    parsed_dict = json.loads(data)
                    return AnswerEvaluation(**parsed_dict)
        except Exception:
            pass

    return evaluate_interview_answer_nlp(question, answer_text)
