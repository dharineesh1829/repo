/**
 * API client module for ResumeMatch AI.
 */
const API = {
  baseUrl: '/api',

  async health() {
    const res = await fetch(`${this.baseUrl}/health`);
    return await res.json();
  },

  async loadDemo() {
    const res = await fetch(`${this.baseUrl}/demo/load`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to load demo data.');
    }
    return await res.json();
  },

  async uploadResume({ file, text, analysisId }) {
    const formData = new FormData();
    if (file) formData.append('file', file);
    if (text) formData.append('text', text);
    if (analysisId) formData.append('analysis_id', analysisId);

    const res = await fetch(`${this.baseUrl}/upload/resume`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Resume upload failed.');
    }
    return await res.json();
  },

  async uploadJD({ file, text, analysisId }) {
    const formData = new FormData();
    if (file) formData.append('file', file);
    if (text) formData.append('text', text);
    if (analysisId) formData.append('analysis_id', analysisId);

    const res = await fetch(`${this.baseUrl}/upload/jd`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Job Description upload failed.');
    }
    return await res.json();
  },

  async executeMatch(analysisId) {
    const res = await fetch(`${this.baseUrl}/match/${analysisId}`, {
      method: 'POST'
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Matching calculation failed.');
    }
    return await res.json();
  },

  async getAnalysis(analysisId) {
    const res = await fetch(`${this.baseUrl}/analysis/${analysisId}`);
    if (!res.ok) throw new Error('Failed to retrieve analysis.');
    return await res.json();
  },

  async listAnalyses() {
    const res = await fetch(`${this.baseUrl}/analyses`);
    if (!res.ok) throw new Error('Failed to retrieve session list.');
    return await res.json();
  },

  async deleteAnalysis(analysisId) {
    const res = await fetch(`${this.baseUrl}/analysis/${analysisId}`, {
      method: 'DELETE'
    });
    if (!res.ok) throw new Error('Failed to delete analysis session.');
    return await res.json();
  },

  async getInterview(analysisId) {
    const res = await fetch(`${this.baseUrl}/interview/${analysisId}`);
    if (!res.ok) throw new Error('Failed to retrieve interview session.');
    return await res.json();
  },

  async submitAnswer(sessionId, questionId, answerText, timeSpent) {
    const res = await fetch(`${this.baseUrl}/interview/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        question_id: questionId,
        answer_text: answerText,
        time_spent_seconds: timeSpent
      })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Evaluation failed.');
    }
    return await res.json();
  },

  async getPreparationReport(analysisId) {
    const res = await fetch(`${this.baseUrl}/interview/${analysisId}/report`);
    if (!res.ok) throw new Error('Failed to retrieve preparation report.');
    return await res.json();
  },

  async getSupabaseStatus() {
    const res = await fetch(`${this.baseUrl}/supabase/status`);
    return await res.json();
  },

  async getSupabaseSchema() {
    const res = await fetch(`${this.baseUrl}/supabase/schema`);
    return await res.json();
  },

  async getSupabaseEmployeeData() {
    const res = await fetch(`${this.baseUrl}/supabase/employee-data`);
    return await res.json();
  },

  async getSupabaseQuestions(analysisId) {
    const url = analysisId ? `${this.baseUrl}/supabase/questions?analysis_id=${encodeURIComponent(analysisId)}` : `${this.baseUrl}/supabase/questions`;
    const res = await fetch(url);
    return await res.json();
  },

  async getSupabasePerformance(analysisId) {
    const url = analysisId ? `${this.baseUrl}/supabase/performance?analysis_id=${encodeURIComponent(analysisId)}` : `${this.baseUrl}/supabase/performance`;
    const res = await fetch(url);
    return await res.json();
  },

  async syncAllToSupabase() {
    const res = await fetch(`${this.baseUrl}/supabase/sync-all`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to sync to Supabase.');
    return await res.json();
  }
};

