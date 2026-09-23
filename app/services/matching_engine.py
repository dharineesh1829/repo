"""
AI/NLP-based Matching Engine for ResumeMatch AI.
Calculates deterministic 5-pillar scores, analyzes eligibility,
and generates in-depth skill gap analysis with learning roadmaps.
"""
import re
from typing import List, Dict, Tuple, Set
from app.models.schemas import (
    ResumeInformation, JobRequirements, MatchResult,
    SkillDetail, EligibilityCheck
)

# Canonical synonym dictionary
SYNONYM_MAP: Dict[str, str] = {
    "reactjs": "react",
    "react.js": "react",
    "react": "react",
    "ml": "machine learning",
    "machine learning": "machine learning",
    "dl": "deep learning",
    "deep learning": "deep learning",
    "tensorflow": "tensorflow",
    "tf": "tensorflow",
    "pytorch": "pytorch",
    "torch": "pytorch",
    "aws": "aws",
    "amazon web services": "aws",
    "gcp": "gcp",
    "google cloud": "gcp",
    "google cloud platform": "gcp",
    "azure": "azure",
    "microsoft azure": "azure",
    "k8s": "kubernetes",
    "kubernetes": "kubernetes",
    "docker": "docker",
    "container": "docker",
    "containers": "docker",
    "containerization": "docker",
    "sql": "sql",
    "mysql": "sql",
    "postgresql": "sql",
    "postgres": "sql",
    "sqlite": "sql",
    "oracle": "sql",
    "mongodb": "mongodb",
    "mongo": "mongodb",
    "nosql": "nosql",
    "js": "javascript",
    "javascript": "javascript",
    "ts": "typescript",
    "typescript": "typescript",
    "git": "git",
    "github": "git",
    "gitlab": "git",
    "rest": "rest apis",
    "rest api": "rest apis",
    "restful": "rest apis",
    "restful api": "rest apis",
    "rest apis": "rest apis",
    "fastapi": "fastapi",
    "flask": "flask",
    "django": "django",
    "ci/cd": "ci/cd",
    "cicd": "ci/cd",
    "continuous integration": "ci/cd",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "pandas": "pandas",
    "numpy": "numpy",
    "nlp": "nlp",
    "natural language processing": "nlp"
}

# Related skills for intelligent partial matching
PARTIAL_MATCH_MAP: Dict[str, Dict[str, str]] = {
    "aws": {
        "related": ["docker", "linux", "cloud computing", "gcp", "azure", "rest apis"],
        "reason": "Candidate has foundational cloud/deployment experience with {related}, but lacks direct hands-on AWS production experience."
    },
    "docker": {
        "related": ["linux", "git", "python", "rest apis", "aws"],
        "reason": "Candidate understands backend services and version control ({related}), which enables rapid onboarding to Docker containerization."
    },
    "kubernetes": {
        "related": ["docker", "aws", "cloud computing", "linux"],
        "reason": "Candidate has foundational container/cloud experience with {related}; Kubernetes represents an orchestration step-up."
    },
    "machine learning": {
        "related": ["python", "sql", "pandas", "numpy", "data science"],
        "reason": "Candidate possesses core data manipulation and programming proficiency ({related}) directly applicable to Machine Learning."
    },
    "deep learning": {
        "related": ["machine learning", "tensorflow", "pytorch", "python"],
        "reason": "Candidate has machine learning and mathematical foundations in {related}, forming a solid base for advanced deep learning."
    },
    "cloud computing": {
        "related": ["aws", "gcp", "azure", "docker", "rest apis"],
        "reason": "Candidate has practical software infrastructure experience with {related}."
    },
    "ci/cd": {
        "related": ["git", "docker", "linux", "testing"],
        "reason": "Candidate uses Git and automated workflows ({related}), facilitating smooth adoption of continuous integration pipelines."
    }
}

# Curated skill gap database for actionable recommendations
SKILL_KNOWLEDGE_BASE: Dict[str, Dict[str, str]] = {
    "aws": {
        "importance": "Critical",
        "why_required": "Modern enterprise applications and ML inference workloads are deployed, scaled, and managed on AWS cloud infrastructure.",
        "learning_direction": "Master core services: AWS EC2 (compute), S3 (object storage), IAM (security), and ECS/Lambda for containerized serverless deployments.",
        "difficulty": "Intermediate",
        "priority": "P1 - Urgent"
    },
    "docker": {
        "importance": "Critical",
        "why_required": "Ensures reproducible runtime environments across local development, CI/CD testing, and production microservices.",
        "learning_direction": "Study Dockerfile syntax, multi-stage builds, container networking, volume mounting, and docker-compose orchestration.",
        "difficulty": "Beginner-Intermediate",
        "priority": "P1 - Urgent"
    },
    "kubernetes": {
        "importance": "High",
        "why_required": "Orchestrates container clusters, auto-scaling, rollouts, and self-healing for high-availability production workloads.",
        "learning_direction": "Learn Pods, Deployments, Services, Ingress controllers, and Helm chart configuration.",
        "difficulty": "Advanced",
        "priority": "P2 - High"
    },
    "sql": {
        "importance": "Critical",
        "why_required": "Essential for relational data modeling, analytical reporting, and feature extraction from enterprise databases.",
        "learning_direction": "Practice complex joins, indexing strategies, CTEs (Common Table Expressions), and window functions.",
        "difficulty": "Beginner-Intermediate",
        "priority": "P1 - Urgent"
    },
    "machine learning": {
        "importance": "Critical",
        "why_required": "Core prerequisite for predictive modeling, feature engineering, and intelligent algorithmic problem-solving.",
        "learning_direction": "Review supervised algorithms (Regression, Random Forests, XGBoost), cross-validation, and ROC-AUC evaluation metrics.",
        "difficulty": "Intermediate",
        "priority": "P1 - Urgent"
    },
    "ci/cd": {
        "importance": "High",
        "why_required": "Automates automated testing, linting, and zero-downtime deployment pipelines for agile teams.",
        "learning_direction": "Build automated pipelines using GitHub Actions or GitLab CI to test and deploy Docker containers.",
        "difficulty": "Intermediate",
        "priority": "P2 - High"
    }
}

EDUCATION_HIERARCHY: Dict[str, int] = {
    "none": 0,
    "high school": 1,
    "diploma": 2,
    "associate": 2,
    "bachelor": 3,
    "bachelor's": 3,
    "b.tech": 3,
    "b.e.": 3,
    "bs": 3,
    "b.s.": 3,
    "master": 4,
    "master's": 4,
    "m.tech": 4,
    "ms": 4,
    "m.s.": 4,
    "mba": 4,
    "phd": 5,
    "ph.d.": 5,
    "doctorate": 5
}

def normalize_skill(skill: str) -> str:
    """Normalizes skill string by stripping punctuation, lowercasing, and resolving synonyms."""
    s = skill.strip().lower()
    s = re.sub(r'[\(\)\[\]\{\},]', '', s)
    return SYNONYM_MAP.get(s, s)

def extract_education_level(text: str) -> int:
    """Identifies the highest education level integer from text."""
    text_lower = text.lower()
    highest = 0
    for key, level in EDUCATION_HIERARCHY.items():
        if re.search(r'\b' + re.escape(key) + r'\b', text_lower):
            if level > highest:
                highest = level
    # Default fallback: if degree contains bachelor, level 3
    if "bachelor" in text_lower or "degree" in text_lower:
        highest = max(highest, 3)
    return highest if highest > 0 else 3 # default to bachelor level if unspecified

def compute_responsibility_overlap(resume: ResumeInformation, jd: JobRequirements) -> int:
    """Computes semantic/token overlap between candidate experience/projects and JD responsibilities."""
    resume_tokens: Set[str] = set()
    for exp in resume.experience:
        resume_tokens.update(re.findall(r'\b[a-zA-Z]{3,}\b', exp.description.lower()))
    for proj in resume.projects:
        resume_tokens.update(re.findall(r'\b[a-zA-Z]{3,}\b', proj.description.lower()))
    if resume.candidate_summary:
        resume_tokens.update(re.findall(r'\b[a-zA-Z]{3,}\b', resume.candidate_summary.lower()))

    # Stopwords to discard
    stopwords = {"and", "the", "with", "for", "from", "that", "this", "our", "are", "have", "been", "using", "work", "team"}
    resume_tokens = {t for t in resume_tokens if t not in stopwords}

    jd_tokens: Set[str] = set()
    for resp in jd.job_responsibilities:
        jd_tokens.update(re.findall(r'\b[a-zA-Z]{3,}\b', resp.lower()))
    jd_tokens = {t for t in jd_tokens if t not in stopwords}

    if not jd_tokens:
        return 85 # standard default if JD had no bullet points

    overlap = resume_tokens.intersection(jd_tokens)
    ratio = len(overlap) / max(1, len(jd_tokens))
    score = min(100, int(ratio * 120)) # scale factor
    return max(40, score) # baseline reasonable score for related domains

def compare_resume_to_jd(resume: ResumeInformation, jd: JobRequirements, engine_type: str = "NLP_RULE_ENGINE") -> MatchResult:
    """
    Executes the complete matching engine:
    1. Skill Matching (Exact, Partial, Missing, Recommended)
    2. Experience Matching
    3. Education Matching
    4. Certification Matching
    5. Responsibility Matching
    6. Overall Match Score Calculation
    7. Eligibility Assessment
    """
    # 1. Normalize candidate skills & tools
    candidate_skills_raw = resume.skills + resume.tools_and_technologies
    candidate_skills_norm: Set[str] = {normalize_skill(s) for s in candidate_skills_raw if s.strip()}
    
    # Also parse skills mentioned inside project descriptions and experience
    for p in resume.projects:
        for tech in p.technologies:
            candidate_skills_norm.add(normalize_skill(tech))
    
    # 2. Normalize JD required skills
    jd_required_raw = jd.required_skills if jd.required_skills else ["Python", "Problem Solving", "Software Engineering"]
    jd_skills_norm: Dict[str, str] = {normalize_skill(s): s for s in jd_required_raw}

    matched_skills: List[str] = []
    missing_skills: List[str] = []
    partially_matched_skills: List[SkillDetail] = []
    all_skill_details: List[SkillDetail] = []

    for norm_skill, original_name in jd_skills_norm.items():
        if norm_skill in candidate_skills_norm:
            # Exact Match
            matched_skills.append(original_name)
            detail = SkillDetail(
                name=original_name,
                status="matched",
                importance="High",
                why_required=f"Directly verified in candidate profile as {original_name}.",
                difficulty_level="Verified",
                estimated_priority="Completed"
            )
            all_skill_details.append(detail)
        else:
            # Check for partial match via related skills
            partial_found = False
            if norm_skill in PARTIAL_MATCH_MAP:
                rule = PARTIAL_MATCH_MAP[norm_skill]
                found_related = [r for r in rule["related"] if normalize_skill(r) in candidate_skills_norm]
                if found_related:
                    partial_found = True
                    matched_with_str = ", ".join(found_related)
                    reason_str = rule["reason"].format(related=matched_with_str)
                    
                    kb_info = SKILL_KNOWLEDGE_BASE.get(norm_skill, {})
                    p_detail = SkillDetail(
                        name=original_name,
                        status="partially_matched",
                        importance=kb_info.get("importance", "High"),
                        why_required=kb_info.get("why_required", f"Essential for the {jd.job_title} role."),
                        suggested_learning_direction=kb_info.get("learning_direction", f"Expand practical knowledge from {matched_with_str} to {original_name}."),
                        difficulty_level=kb_info.get("difficulty", "Intermediate"),
                        estimated_priority="P2 - High",
                        matched_with=matched_with_str,
                        partial_reason=reason_str
                    )
                    partially_matched_skills.append(p_detail)
                    all_skill_details.append(p_detail)

            if not partial_found:
                # Skill is Missing
                missing_skills.append(original_name)
                kb_info = SKILL_KNOWLEDGE_BASE.get(norm_skill, {})
                m_detail = SkillDetail(
                    name=original_name,
                    status="missing",
                    importance=kb_info.get("importance", "High"),
                    why_required=kb_info.get("why_required", f"Required by {jd.company} for {jd.job_title} day-to-day operations."),
                    suggested_learning_direction=kb_info.get("learning_direction", f"Follow an introductory hands-on roadmap to acquire foundational proficiency in {original_name}."),
                    difficulty_level=kb_info.get("difficulty", "Intermediate"),
                    estimated_priority=kb_info.get("priority", "P1 - Urgent")
                )
                all_skill_details.append(m_detail)

    # 3. Recommended Skills (Skills that add high value to this role)
    recommended_skills: List[SkillDetail] = []
    standard_recs = ["AWS", "Docker", "CI/CD", "MLOps", "FastAPI"]
    for rec in standard_recs:
        norm_rec = normalize_skill(rec)
        if norm_rec not in candidate_skills_norm:
            kb_info = SKILL_KNOWLEDGE_BASE.get(norm_rec, {})
            r_detail = SkillDetail(
                name=rec,
                status="recommended",
                importance=kb_info.get("importance", "Medium"),
                why_required=kb_info.get("why_required", "Emerging high-demand capability that significantly elevates candidate marketability."),
                suggested_learning_direction=kb_info.get("learning_direction", f"Explore practical tutorials and mini-projects integrating {rec}."),
                difficulty_level=kb_info.get("difficulty", "Intermediate"),
                estimated_priority="P2 - High"
            )
            recommended_skills.append(r_detail)

    # ==========================================
    # 4. 5-Pillar Score Computation
    # ==========================================
    
    # A. Skill Match Score (Weight: 40%)
    total_req_skills = max(1, len(jd_skills_norm))
    # Full credit for matched, 0.6 credit for partially matched
    skill_score_raw = ((len(matched_skills) * 1.0) + (len(partially_matched_skills) * 0.6)) / total_req_skills * 100
    skill_match_score = min(100, max(10, int(skill_score_raw)))

    # B. Experience Match Score (Weight: 25%)
    cand_years = float(resume.total_experience_years)
    req_years = float(jd.min_experience_years) if jd.min_experience_years > 0 else 1.0
    
    if cand_years >= req_years:
        exp_score = 100
    else:
        # Give partial credit for internships and academic projects
        ratio = cand_years / req_years
        exp_score = int(ratio * 75) + (20 if len(resume.projects) >= 2 else 10)
    experience_match_score = min(100, max(25, exp_score))

    # C. Education Match Score (Weight: 15%)
    cand_edu_level = 0
    for edu in resume.education:
        cand_edu_level = max(cand_edu_level, extract_education_level(edu.degree))
    if cand_edu_level == 0:
        cand_edu_level = 3 # default Bachelor's if detected in text
    
    req_edu_level = extract_education_level(jd.education_requirements) or 3
    if cand_edu_level >= req_edu_level:
        education_match_score = 100
    elif cand_edu_level == req_edu_level - 1:
        education_match_score = 80
    else:
        education_match_score = 60

    # D. Certification Match Score (Weight: 10%)
    if jd.certifications_required:
        matched_certs = [c for c in resume.certifications if any(normalize_skill(rc) in normalize_skill(c) for rc in jd.certifications_required)]
        cert_score = int((len(matched_certs) / len(jd.certifications_required)) * 100)
    else:
        # If JD has no mandatory certs, having certs gives 100%, none gives 85%
        cert_score = 100 if len(resume.certifications) > 0 else 85
    certification_match_score = min(100, max(30, cert_score))

    # E. Responsibility Match Score (Weight: 10%)
    responsibility_match_score = compute_responsibility_overlap(resume, jd)

    # Overall Composite Score (0-100)
    overall_score = int(
        (0.40 * skill_match_score) +
        (0.25 * experience_match_score) +
        (0.15 * education_match_score) +
        (0.10 * certification_match_score) +
        (0.10 * responsibility_match_score)
    )
    overall_score = min(100, max(0, overall_score))

    # ==========================================
    # 5. Eligibility Analysis
    # ==========================================
    eligibility_checks: List[EligibilityCheck] = []
    
    # Check 1: Education
    cand_degree_str = resume.education[0].degree if resume.education else "Bachelor of Science"
    edu_satisfied = cand_edu_level >= req_edu_level
    eligibility_checks.append(EligibilityCheck(
        criterion="Education Level",
        status="satisfied" if edu_satisfied else "partially_satisfied",
        candidate_value=cand_degree_str,
        required_value=jd.education_requirements if jd.education_requirements else "Bachelor's Degree in STEM",
        explanation=f"Candidate holds a recognized degree ({cand_degree_str}) that satisfies the minimum requirement." if edu_satisfied else "Candidate degree level is slightly below the preferred degree level."
    ))

    # Check 2: Minimum Experience
    exp_satisfied = cand_years >= req_years
    cand_exp_str = f"{cand_years:.1f} years" if cand_years > 0 else "Fresh Graduate / Internship"
    req_exp_str = f"{req_years:.0f}+ years"
    
    if exp_satisfied:
        exp_status = "satisfied"
        exp_expl = f"Candidate satisfies the {req_exp_str} professional experience threshold."
    elif cand_years >= (req_years * 0.4):
        exp_status = "partially_satisfied"
        exp_expl = f"Candidate has {cand_exp_str} experience (including internships/projects) vs {req_exp_str} required. Suitable for high-potential or fast-track entry."
    else:
        exp_status = "not_satisfied"
        exp_expl = f"Candidate has {cand_exp_str} vs {req_exp_str} required. Significant experience gap."
    
    eligibility_checks.append(EligibilityCheck(
        criterion="Minimum Experience",
        status=exp_status,
        candidate_value=cand_exp_str,
        required_value=req_exp_str,
        explanation=exp_expl
    ))

    # Check 3: Core Technical Skills
    core_skill_ratio = (len(matched_skills) + len(partially_matched_skills)) / total_req_skills
    if core_skill_ratio >= 0.70:
        skill_status = "satisfied"
        skill_expl = f"Candidate covers {int(core_skill_ratio*100)}% of the essential technical skills requested by the employer."
    elif core_skill_ratio >= 0.45:
        skill_status = "partially_satisfied"
        skill_expl = f"Candidate possesses core foundations ({', '.join(matched_skills[:3])}) but needs to ramp up on secondary skills ({', '.join(missing_skills[:2])})."
    else:
        skill_status = "not_satisfied"
        skill_expl = f"Candidate covers less than 45% of the mandatory technical skills."
    
    eligibility_checks.append(EligibilityCheck(
        criterion="Core Technical Skills",
        status=skill_status,
        candidate_value=f"{len(matched_skills)} matched, {len(partially_matched_skills)} partial",
        required_value=f"{total_req_skills} core skills",
        explanation=skill_expl
    ))

    # Overall Eligibility Status Decision
    not_sat_count = sum(1 for c in eligibility_checks if c.status == "not_satisfied")
    part_sat_count = sum(1 for c in eligibility_checks if c.status == "partially_satisfied")

    if not_sat_count == 0 and part_sat_count <= 1 and overall_score >= 70:
        eligibility_status = "Eligible"
        eligibility_summary = "The candidate strongly meets the baseline education, technical capabilities, and role requirements."
    elif not_sat_count <= 1 and overall_score >= 50:
        eligibility_status = "Partially Eligible"
        eligibility_summary = "The candidate meets foundational technical requirements, with a slight experience or tooling gap (e.g. AWS/Docker) that can be bridged with targeted preparation."
    else:
        eligibility_status = "Not Eligible"
        eligibility_summary = "Significant gaps exist in required experience or core mandatory technical competencies."

    # 6. Candidate Strengths & Areas to Improve
    strengths = []
    if matched_skills:
        strengths.append(f"Strong foundation in core technical stack: {', '.join(matched_skills)}.")
    if cand_edu_level >= 3:
        strengths.append("Meets academic degree requirements in Computer Science / Engineering.")
    if len(resume.projects) > 0:
        strengths.append(f"Demonstrated project portfolio with {len(resume.projects)} practical implementations.")
    if len(resume.experience) > 0:
        strengths.append(f"Practical real-world experience demonstrated during internship/employment ({resume.experience[0].title}).")

    areas_to_improve = []
    for m in missing_skills[:3]:
        areas_to_improve.append(f"Acquire hands-on deployment experience with {m} to fulfill production readiness criteria.")
    if exp_status != "satisfied":
        areas_to_improve.append("Highlight transferable project accomplishments and system design depth to offset lower total years of tenure.")

    return MatchResult(
        overall_score=overall_score,
        skill_match_score=skill_match_score,
        experience_match_score=experience_match_score,
        education_match_score=education_match_score,
        certification_match_score=certification_match_score,
        responsibility_match_score=responsibility_match_score,
        eligibility_status=eligibility_status,
        eligibility_summary=eligibility_summary,
        eligibility_checks=eligibility_checks,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        partially_matched_skills=partially_matched_skills,
        recommended_skills=recommended_skills,
        all_skill_details=all_skill_details,
        strengths=strengths,
        areas_to_improve=areas_to_improve,
        engine_used=engine_type
    )
