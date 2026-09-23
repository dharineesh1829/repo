"""
Pydantic schemas and data contracts for ResumeMatch AI.
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

# ==========================================
# 1. Resume & JD Extracted Models
# ==========================================

class ResumeExperienceItem(BaseModel):
    title: str = Field(..., description="Job title or role")
    company: str = Field(default="", description="Company or organization name")
    duration: str = Field(default="", description="Duration e.g., '6 months', '2023 - Present'")
    description: str = Field(default="", description="Key responsibilities or bullet points")

class ResumeEducationItem(BaseModel):
    degree: str = Field(..., description="Degree name, e.g., Bachelor of Science")
    institution: str = Field(default="", description="University or college")
    year: str = Field(default="", description="Graduation year or date range")
    details: str = Field(default="", description="GPA, coursework, honors")

class ResumeProjectItem(BaseModel):
    name: str = Field(..., description="Project title")
    technologies: List[str] = Field(default_factory=list, description="Technologies used")
    description: str = Field(default="", description="Project details and outcomes")

class ResumeInformation(BaseModel):
    candidate_name: str = Field(default="Candidate", description="Detected name")
    candidate_email: Optional[str] = None
    candidate_phone: Optional[str] = None
    candidate_summary: str = Field(default="", description="Executive or professional summary")
    skills: List[str] = Field(default_factory=list, description="List of detected skills")
    tools_and_technologies: List[str] = Field(default_factory=list, description="Specific developer tools, frameworks, and tech")
    total_experience_years: float = Field(default=0.0, description="Calculated total years of experience")
    experience: List[ResumeExperienceItem] = Field(default_factory=list, description="List of work experiences")
    education: List[ResumeEducationItem] = Field(default_factory=list, description="List of degrees and education")
    certifications: List[str] = Field(default_factory=list, description="Certifications and licenses")
    projects: List[ResumeProjectItem] = Field(default_factory=list, description="Notable academic and personal projects")

class JobRequirements(BaseModel):
    job_title: str = Field(default="Target Role", description="Job title")
    company: str = Field(default="Company", description="Hiring company")
    required_skills: List[str] = Field(default_factory=list, description="Must-have technical and domain skills")
    preferred_skills: List[str] = Field(default_factory=list, description="Nice-to-have skills")
    tools_and_technologies: List[str] = Field(default_factory=list, description="Required frameworks, clouds, and tools")
    experience_requirements: str = Field(default="", description="Experience requirement text")
    min_experience_years: float = Field(default=0.0, description="Minimum numeric years required")
    education_requirements: str = Field(default="", description="Required education e.g., Bachelor's in CS")
    min_education_level: str = Field(default="Bachelor's", description="Minimum level: None, High School, Diploma, Bachelor's, Master's, PhD")
    certifications_required: List[str] = Field(default_factory=list, description="Mandatory or preferred certifications")
    job_responsibilities: List[str] = Field(default_factory=list, description="Core responsibilities and duties")

# ==========================================
# 2. Comparison & Skill Gap Models
# ==========================================

class SkillDetail(BaseModel):
    name: str
    status: str = Field(..., description="'matched', 'missing', 'partially_matched', 'recommended'")
    importance: str = Field(default="High", description="'Critical', 'High', 'Medium', 'Low'")
    why_required: str = Field(default="", description="Context on why this skill is needed for this role")
    suggested_learning_direction: str = Field(default="", description="Learning resources or conceptual path")
    difficulty_level: str = Field(default="Intermediate", description="'Beginner', 'Intermediate', 'Advanced'")
    estimated_priority: str = Field(default="P1", description="'P1 - Urgent', 'P2 - High', 'P3 - Medium'")
    matched_with: Optional[str] = None
    partial_reason: Optional[str] = None

class EligibilityCheck(BaseModel):
    criterion: str
    status: str = Field(..., description="'satisfied', 'partially_satisfied', 'not_satisfied'")
    candidate_value: str
    required_value: str
    explanation: str

class MatchResult(BaseModel):
    overall_score: int = Field(..., ge=0, le=100, description="Composite match score 0-100")
    skill_match_score: int = Field(..., ge=0, le=100)
    experience_match_score: int = Field(..., ge=0, le=100)
    education_match_score: int = Field(..., ge=0, le=100)
    certification_match_score: int = Field(..., ge=0, le=100)
    responsibility_match_score: int = Field(..., ge=0, le=100)
    
    eligibility_status: str = Field(..., description="'Eligible', 'Partially Eligible', 'Not Eligible'")
    eligibility_summary: str
    eligibility_checks: List[EligibilityCheck] = Field(default_factory=list)
    
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    partially_matched_skills: List[SkillDetail] = Field(default_factory=list)
    recommended_skills: List[SkillDetail] = Field(default_factory=list)
    all_skill_details: List[SkillDetail] = Field(default_factory=list)
    
    strengths: List[str] = Field(default_factory=list)
    areas_to_improve: List[str] = Field(default_factory=list)
    engine_used: str = Field(default="NLP_RULE_ENGINE", description="'LIVE_LLM' or 'NLP_RULE_ENGINE'")

# ==========================================
# 3. Mock Interview & Evaluation Models
# ==========================================

class InterviewQuestion(BaseModel):
    id: str
    category: str = Field(..., description="'HR', 'Technical', 'Behavioral', 'Resume-Based', 'JD-Specific'")
    question_text: str
    context_source: str = Field(default="", description="Why this question was generated from candidate resume or JD")
    order_index: int = 0

class AnswerEvaluation(BaseModel):
    technical_accuracy_score: int = Field(default=8, ge=0, le=10)
    relevance_score: int = Field(default=8, ge=0, le=10)
    completeness_score: int = Field(default=8, ge=0, le=10)
    communication_score: int = Field(default=8, ge=0, le=10)
    overall_score: int = Field(default=8, ge=0, le=10)
    confidence_indicators: List[str] = Field(default_factory=list)
    missing_points: List[str] = Field(default_factory=list)
    what_you_did_well: List[str] = Field(default_factory=list)
    what_you_can_improve: List[str] = Field(default_factory=list)
    better_answer_approach: str = Field(default="")

class InterviewAnswer(BaseModel):
    question_id: str
    question_category: str
    question_text: str
    user_answer: str
    time_spent_seconds: int = 0
    evaluation: Optional[AnswerEvaluation] = None

class InterviewSession(BaseModel):
    id: str
    analysis_id: str
    questions: List[InterviewQuestion] = Field(default_factory=list)
    answers: Dict[str, InterviewAnswer] = Field(default_factory=dict)
    current_index: int = 0
    is_completed: bool = False
    average_interview_score: float = 0.0

# ==========================================
# 4. Final Preparation Report Model
# ==========================================

class PreparationChecklistItem(BaseModel):
    id: str
    title: str
    category: str
    completed: bool = False
    description: str

class FinalPreparationReport(BaseModel):
    analysis_id: str
    candidate_name: str
    job_title: str
    overall_match_score: int
    eligibility_status: str
    interview_average_score: float
    top_strengths: List[str]
    skill_gaps: List[str]
    recommended_skills: List[str]
    interview_strengths: List[str]
    interview_weaknesses: List[str]
    questions_needing_prep: List[Dict[str, Any]]
    recommended_topics: List[str]
    checklist: List[PreparationChecklistItem]
    generated_at: str

# ==========================================
# 5. API Request / Response Wrappers
# ==========================================

class TextUploadRequest(BaseModel):
    text: str
    title: Optional[str] = "Pasted Content"

class MatchRequest(BaseModel):
    analysis_id: str

class SubmitAnswerRequest(BaseModel):
    session_id: str
    question_id: str
    answer_text: str
    time_spent_seconds: int = 0

class AnalysisSummary(BaseModel):
    id: str
    created_at: str
    candidate_name: str
    job_title: str
    overall_match_score: Optional[int] = None
    eligibility_status: Optional[str] = None
    engine_used: str = "NLP_RULE_ENGINE"
