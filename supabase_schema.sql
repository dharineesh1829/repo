-- =========================================================================
-- ResumeMatch AI - Unified Supabase Master Database Schema
-- Run this script in the Supabase SQL Editor:
-- https://supabase.com/dashboard/project/ymcnojaywvmyzjzyxwxe/sql
-- =========================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. EMPLOYEE & CANDIDATE DATA TABLE ("EMPLOY DTAT")
CREATE TABLE IF NOT EXISTS public.employee_data (
    id TEXT PRIMARY KEY,
    candidate_name TEXT DEFAULT 'Candidate',
    email TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    title TEXT DEFAULT 'Resume Analysis',
    resume_filename TEXT DEFAULT '',
    resume_raw TEXT DEFAULT '',
    resume_parsed JSONB DEFAULT '{}'::jsonb,
    job_title TEXT DEFAULT 'Target Position',
    jd_filename TEXT DEFAULT '',
    jd_raw TEXT DEFAULT '',
    jd_parsed JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. INTERVIEW QUESTIONS TABLE ("QUTION")
CREATE TABLE IF NOT EXISTS public.questions (
    id TEXT PRIMARY KEY,
    analysis_id TEXT REFERENCES public.employee_data(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    question_text TEXT NOT NULL,
    context_source TEXT DEFAULT '',
    order_index INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. CANDIDATE PERFORMANCE DETAILS TABLE ("THERE PREFORMANCE DETAIL")
CREATE TABLE IF NOT EXISTS public.performance_details (
    id TEXT PRIMARY KEY,
    analysis_id TEXT REFERENCES public.employee_data(id) ON DELETE CASCADE,
    candidate_name TEXT DEFAULT '',
    job_title TEXT DEFAULT '',
    overall_match_score NUMERIC DEFAULT 0,
    skill_match_score NUMERIC DEFAULT 0,
    experience_match_score NUMERIC DEFAULT 0,
    eligibility_status TEXT DEFAULT 'Pending Evaluation',
    matched_skills JSONB DEFAULT '[]'::jsonb,
    missing_skills JSONB DEFAULT '[]'::jsonb,
    average_interview_score NUMERIC DEFAULT 0,
    answers_evaluations JSONB DEFAULT '{}'::jsonb,
    preparation_report JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. 300,000+ TECHNICAL QUESTION REPOSITORY BANK
CREATE TABLE IF NOT EXISTS public.technical_question_bank (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    language VARCHAR(32) NOT NULL 
        CHECK (language IN ('Python', 'C', 'C++', 'HTML', 'Java', 'Rust')),
    difficulty VARCHAR(20) NOT NULL 
        CHECK (difficulty IN ('Beginner', 'Intermediate', 'Advanced')),
    topic VARCHAR(80) NOT NULL,
    subtopic VARCHAR(80) DEFAULT '',
    question_type VARCHAR(32) NOT NULL DEFAULT 'code_output' 
        CHECK (question_type IN ('code_output', 'conceptual', 'multiple_choice', 'debugging', 'architecture')),
    title VARCHAR(255) NOT NULL,
    question_text TEXT NOT NULL,
    code_snippet TEXT DEFAULT '',
    options JSONB DEFAULT '[]'::jsonb,
    expected_answer TEXT NOT NULL,
    explanation TEXT NOT NULL,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    experience_level_target VARCHAR(20) DEFAULT 'Mid-Level' 
        CHECK (experience_level_target IN ('Entry', 'Mid-Level', 'Senior', 'Staff')),
    time_limit_seconds INT DEFAULT 90 CHECK (time_limit_seconds BETWEEN 15 AND 600),
    content_hash CHAR(64) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- INDEXES
CREATE INDEX IF NOT EXISTS idx_questions_analysis_id ON public.questions(analysis_id);
CREATE INDEX IF NOT EXISTS idx_perf_analysis_id ON public.performance_details(analysis_id);
CREATE INDEX IF NOT EXISTS idx_tqb_lang_diff_active ON public.technical_question_bank (language, difficulty) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_tqb_lang_topic ON public.technical_question_bank (language, topic) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_tqb_tags_gin ON public.technical_question_bank USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_tqb_content_hash ON public.technical_question_bank (content_hash);

-- RLS POLICIES (FULL PERMISSIONS FOR ANON / PUBLISHABLE KEY & SERVICE ROLE)
ALTER TABLE public.employee_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.performance_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.technical_question_bank ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow all on employee_data" ON public.employee_data;
CREATE POLICY "Allow all on employee_data" ON public.employee_data FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow all on questions" ON public.questions;
CREATE POLICY "Allow all on questions" ON public.questions FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow all on performance_details" ON public.performance_details;
CREATE POLICY "Allow all on performance_details" ON public.performance_details FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow all on technical_question_bank" ON public.technical_question_bank;
CREATE POLICY "Allow all on technical_question_bank" ON public.technical_question_bank FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

