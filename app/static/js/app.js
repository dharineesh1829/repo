/**
 * ResumeMatch AI - Application Controller & State Manager
 */

// Application State
const State = {
  currentAnalysisId: null,
  analysisData: null,
  interviewSession: null,
  activeQuestionIndex: 0,
  interviewTimerInterval: null,
  interviewTimeSeconds: 0,
  speechRecognition: null,
  isListening: false,
  checklistState: {}
};

// ==========================================
// Initialization & Navigation
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initUploadListeners();
  initInterviewListeners();
  initSpeechRecognition();
  checkBackendHealth();
});

function initNavigation() {
  const navLinks = document.querySelectorAll('.nav-link');
  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const targetView = link.getAttribute('data-view');
      switchView(targetView);
    });
  });

  // Mobile menu toggle
  const mobileBtn = document.getElementById('btn-mobile-menu');
  const sidebar = document.getElementById('app-sidebar');
  if (mobileBtn && sidebar) {
    mobileBtn.addEventListener('click', () => {
      sidebar.classList.toggle('open');
    });
  }
}

function switchView(viewName) {
  // Update nav active link
  document.querySelectorAll('.nav-link').forEach(link => {
    if (link.getAttribute('data-view') === viewName) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });

  // Toggle view sections
  document.querySelectorAll('.view-section').forEach(sec => {
    sec.classList.remove('active');
  });

  const activeSec = document.getElementById(`view-${viewName}`);
  if (activeSec) {
    activeSec.classList.add('active');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // View-specific render callbacks
  if (viewName === 'dashboard') renderDashboard();
  if (viewName === 'job-match') renderJobMatchView();
  if (viewName === 'skill-gap') renderSkillGapView();
  if (viewName === 'job-fit-report') renderJobFitReportView();
  if (viewName === 'mock-interview') renderMockInterviewChamber();
  if (viewName === 'interview-results') renderInterviewResults();
  if (viewName === 'preparation-report') renderPreparationReport();
  if (viewName === 'supabase-dashboard') renderSupabaseDashboard();

  // Close mobile sidebar if open
  const sidebar = document.getElementById('app-sidebar');
  if (sidebar && sidebar.classList.contains('open')) {
    sidebar.classList.remove('open');
  }
}

async function checkBackendHealth() {
  try {
    const health = await API.health();
    const tag = document.getElementById('sidebar-engine-status');
    if (tag) {
      if (health.llm_available) {
        tag.innerHTML = `<span class="status-dot"></span> Live AI (${health.model})`;
      } else {
        tag.innerHTML = `<span class="status-dot"></span> Demo/NLP Engine`;
      }
    }

    const sbTag = document.getElementById('sidebar-supabase-status');
    if (sbTag) {
      if (health.supabase_configured) {
        sbTag.innerHTML = `<span class="status-dot" style="background:#00d18f;"></span> Supabase: Online`;
      } else {
        sbTag.innerHTML = `<span class="status-dot" style="background:#f59e0b;"></span> Supabase: Offline`;
      }
    }
  } catch (e) {
    console.warn('Backend health check error:', e);
  }
}


// ==========================================
// Demo Mode Handler
// ==========================================
async function loadDemoMode() {
  showToast('Loading full demo dataset...', 'info');
  try {
    const data = await API.loadDemo();
    State.currentAnalysisId = data.analysis_id;
    State.analysisData = {
      id: data.analysis_id,
      resume_parsed: data.resume,
      jd_parsed: data.job_description,
      match_result: data.match_result,
      resume_filename: "sample_resume.txt (Demo Data)",
      jd_filename: "sample_job_description.txt (Demo Data)"
    };
    State.interviewSession = data.interview_session;
    State.activeQuestionIndex = 0;

    // Refresh Supabase dashboard in background
    renderSupabaseDashboard().catch(() => {});


    showToast('Demo data loaded successfully! Inspecting match results...', 'success');
    switchView('dashboard');
  } catch (err) {
    showToast(err.message || 'Error loading demo data', 'error');
  }
}

// ==========================================
// Toast Notifications
// ==========================================
function showToast(message, type = 'info') {
  let toastContainer = document.getElementById('toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    toastContainer.style.position = 'fixed';
    toastContainer.style.bottom = '24px';
    toastContainer.style.right = '24px';
    toastContainer.style.zIndex = '9999';
    toastContainer.style.display = 'flex';
    toastContainer.style.flexDirection = 'column';
    toastContainer.style.gap = '10px';
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement('div');
  toast.style.padding = '12px 20px';
  toast.style.borderRadius = '8px';
  toast.style.color = '#fff';
  toast.style.fontSize = '0.9rem';
  toast.style.fontWeight = '500';
  toast.style.boxShadow = '0 10px 25px rgba(0,0,0,0.5)';
  toast.style.backdropFilter = 'blur(10px)';
  toast.style.display = 'flex';
  toast.style.alignItems = 'center';
  toast.style.gap = '10px';
  toast.style.animation = 'fadeIn 0.2s ease-out';

  if (type === 'success') {
    toast.style.background = 'rgba(16, 185, 129, 0.9)';
    toast.style.border = '1px solid #10b981';
    toast.innerHTML = `✓ ${message}`;
  } else if (type === 'error') {
    toast.style.background = 'rgba(239, 68, 68, 0.9)';
    toast.style.border = '1px solid #ef4444';
    toast.innerHTML = `⚠️ ${message}`;
  } else {
    toast.style.background = 'rgba(0, 210, 255, 0.85)';
    toast.style.border = '1px solid #00d2ff';
    toast.style.color = '#000';
    toast.innerHTML = `ℹ️ ${message}`;
  }

  toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ==========================================
// Document Upload & Parsing Handlers
// ==========================================
let selectedResumeFile = null;
let selectedJdFile = null;

function initUploadListeners() {
  // Tab Switching for Resume Upload
  const resumeTabs = document.querySelectorAll('#resume-tabs .tab-btn');
  resumeTabs.forEach(btn => {
    btn.addEventListener('click', () => {
      resumeTabs.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const mode = btn.getAttribute('data-tab');
      document.getElementById('resume-file-pane').style.display = mode === 'file' ? 'block' : 'none';
      document.getElementById('resume-paste-pane').style.display = mode === 'paste' ? 'block' : 'none';
    });
  });

  // Tab Switching for JD Upload
  const jdTabs = document.querySelectorAll('#jd-tabs .tab-btn');
  jdTabs.forEach(btn => {
    btn.addEventListener('click', () => {
      jdTabs.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const mode = btn.getAttribute('data-tab');
      document.getElementById('jd-file-pane').style.display = mode === 'file' ? 'block' : 'none';
      document.getElementById('jd-paste-pane').style.display = mode === 'paste' ? 'block' : 'none';
    });
  });

  // Resume File Drag & Drop
  const resumeDropZone = document.getElementById('resume-drop-zone');
  const resumeFileInput = document.getElementById('resume-file-input');

  if (resumeDropZone && resumeFileInput) {
    resumeDropZone.addEventListener('click', () => resumeFileInput.click());
    resumeDropZone.addEventListener('dragover', (e) => { e.preventDefault(); resumeDropZone.classList.add('dragover'); });
    resumeDropZone.addEventListener('dragleave', () => resumeDropZone.classList.remove('dragover'));
    resumeDropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      resumeDropZone.classList.remove('dragover');
      if (e.dataTransfer.files.length) handleResumeFile(e.dataTransfer.files[0]);
    });
    resumeFileInput.addEventListener('change', (e) => {
      if (e.target.files.length) handleResumeFile(e.target.files[0]);
    });
  }

  // JD File Drag & Drop
  const jdDropZone = document.getElementById('jd-drop-zone');
  const jdFileInput = document.getElementById('jd-file-input');

  if (jdDropZone && jdFileInput) {
    jdDropZone.addEventListener('click', () => jdFileInput.click());
    jdDropZone.addEventListener('dragover', (e) => { e.preventDefault(); jdDropZone.classList.add('dragover'); });
    jdDropZone.addEventListener('dragleave', () => jdDropZone.classList.remove('dragover'));
    jdDropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      jdDropZone.classList.remove('dragover');
      if (e.dataTransfer.files.length) handleJdFile(e.dataTransfer.files[0]);
    });
    jdFileInput.addEventListener('change', (e) => {
      if (e.target.files.length) handleJdFile(e.target.files[0]);
    });
  }
}

function handleResumeFile(file) {
  selectedResumeFile = file;
  const chip = document.getElementById('resume-file-chip');
  if (chip) {
    chip.style.display = 'inline-flex';
    chip.innerHTML = `📄 <strong>${file.name}</strong> (${(file.size / 1024).toFixed(1)} KB)`;
  }
}

function handleJdFile(file) {
  selectedJdFile = file;
  const chip = document.getElementById('jd-file-chip');
  if (chip) {
    chip.style.display = 'inline-flex';
    chip.innerHTML = `💼 <strong>${file.name}</strong> (${(file.size / 1024).toFixed(1)} KB)`;
  }
}

function populateSampleResumeText() {
  const txt = document.getElementById('resume-paste-text');
  if (txt && window.DEMO_DATA) {
    txt.value = DEMO_DATA.resumeText;
    showToast('Loaded sample resume text into paste box', 'info');
  }
}

function populateSampleJdText() {
  const txt = document.getElementById('jd-paste-text');
  if (txt && window.DEMO_DATA) {
    txt.value = DEMO_DATA.jdText;
    showToast('Loaded sample job description into paste box', 'info');
  }
}

// Resume Process Animation
async function submitResume() {
  const isPaste = document.querySelector('#resume-tabs .tab-btn[data-tab="paste"]').classList.contains('active');
  const pasteText = document.getElementById('resume-paste-text').value.trim();

  if (!isPaste && !selectedResumeFile) {
    showToast('Please select a resume file (PDF/DOCX/TXT) or paste text.', 'error');
    return;
  }
  if (isPaste && !pasteText) {
    showToast('Please paste your resume text.', 'error');
    return;
  }

  // Show processing overlay
  const overlay = document.getElementById('resume-parsing-overlay');
  overlay.style.display = 'block';

  const steps = [
    'Parsing Resume...',
    'Extracting Skills & Technologies...',
    'Analyzing Work Experience...',
    'Understanding Education History...',
    'Reading Certifications...',
    'Analyzing Projects...'
  ];

  for (let i = 0; i < steps.length; i++) {
    await animateStep('resume-step-', i);
  }

  try {
    const res = await API.uploadResume({
      file: isPaste ? null : selectedResumeFile,
      text: isPaste ? pasteText : null,
      analysisId: State.currentAnalysisId
    });

    State.currentAnalysisId = res.analysis_id;
    if (!State.analysisData) State.analysisData = { id: res.analysis_id };
    State.analysisData.resume_parsed = res.parsed_data;
    State.analysisData.resume_filename = res.filename;

    overlay.style.display = 'none';
    showToast('Resume parsed successfully!', 'success');
    renderResumeParsedPreview(res.parsed_data);
  } catch (err) {
    overlay.style.display = 'none';
    showToast(err.message || 'Error processing resume', 'error');
  }
}

// JD Process Animation
async function submitJobDescription() {
  const isPaste = document.querySelector('#jd-tabs .tab-btn[data-tab="paste"]').classList.contains('active');
  const pasteText = document.getElementById('jd-paste-text').value.trim();

  if (!isPaste && !selectedJdFile) {
    showToast('Please select a JD file (PDF/DOCX/TXT) or paste text.', 'error');
    return;
  }
  if (isPaste && !pasteText) {
    showToast('Please paste your job description text.', 'error');
    return;
  }

  const overlay = document.getElementById('jd-parsing-overlay');
  overlay.style.display = 'block';

  const steps = [
    'Parsing Job Description...',
    'Extracting Required Skills...',
    'Analyzing Responsibilities...',
    'Analyzing Experience Requirements...',
    'Analyzing Education Requirements...'
  ];

  for (let i = 0; i < steps.length; i++) {
    await animateStep('jd-step-', i);
  }

  try {
    const res = await API.uploadJD({
      file: isPaste ? null : selectedJdFile,
      text: isPaste ? pasteText : null,
      analysisId: State.currentAnalysisId
    });

    State.currentAnalysisId = res.analysis_id;
    if (!State.analysisData) State.analysisData = { id: res.analysis_id };
    State.analysisData.jd_parsed = res.parsed_data;
    State.analysisData.jd_filename = res.filename;

    overlay.style.display = 'none';
    showToast('Job Description parsed successfully!', 'success');
    renderJdParsedPreview(res.parsed_data);
  } catch (err) {
    overlay.style.display = 'none';
    showToast(err.message || 'Error processing JD', 'error');
  }
}

function animateStep(prefix, index) {
  return new Promise(resolve => {
    const el = document.getElementById(`${prefix}${index}`);
    if (el) {
      el.classList.add('active');
      setTimeout(() => {
        el.classList.remove('active');
        el.classList.add('completed');
        const icon = el.querySelector('.step-circle');
        if (icon) icon.innerHTML = '✓';
        resolve();
      }, 250);
    } else {
      resolve();
    }
  });
}

// Trigger comparison match
async function triggerMatchAndCompare() {
  if (!State.currentAnalysisId) {
    showToast('Please upload both a resume and job description first.', 'error');
    return;
  }
  showToast('Comparing Resume with Job Requirements...', 'info');
  try {
    const res = await API.executeMatch(State.currentAnalysisId);
    State.analysisData.match_result = res.match_result;
    
    // Fetch interview session
    const interview = await API.getInterview(State.currentAnalysisId);
    State.interviewSession = interview;
    State.activeQuestionIndex = 0;

    showToast('Match calculated! Proceeding to Job Match view.', 'success');
    switchView('job-match');
  } catch (err) {
    showToast(err.message || 'Failed to compare resume and JD', 'error');
  }
}

// ==========================================
// RENDERERS
// ==========================================

function renderResumeParsedPreview(data) {
  const container = document.getElementById('resume-parsed-preview');
  if (!container) return;
  container.style.display = 'block';

  let skillsBadges = (data.skills || []).map(s => `<span class="skill-badge matched">${s}</span>`).join(' ');
  let toolsBadges = (data.tools_and_technologies || []).map(t => `<span class="skill-badge recommended">${t}</span>`).join(' ');

  let expHtml = (data.experience || []).map(e => `
    <div style="margin-bottom: 12px; padding: 12px; background: rgba(255,255,255,0.03); border-radius: 8px;">
      <div style="font-weight: 600; color: #fff;">${e.title} ${e.company ? `• <span style="color: var(--primary);">${e.company}</span>` : ''}</div>
      <div style="font-size: 0.8rem; color: var(--text-dim); margin-bottom: 4px;">${e.duration}</div>
      <div style="font-size: 0.88rem; color: var(--text-muted);">${e.description}</div>
    </div>
  `).join('');

  let eduHtml = (data.education || []).map(ed => `
    <div style="margin-bottom: 8px;">
      <strong>${ed.degree}</strong> - ${ed.institution} (${ed.year})
    </div>
  `).join('');

  container.innerHTML = `
    <div style="margin-top: 24px; border-top: 1px solid var(--border-subtle); padding-top: 20px;">
      <h3 style="font-family: var(--font-heading); margin-bottom: 16px; color: var(--primary);">✓ Extracted Resume Data: ${data.candidate_name}</h3>
      <div style="margin-bottom: 16px;">
        <div style="font-size: 0.8rem; text-transform: uppercase; color: var(--text-dim); font-weight: 700; margin-bottom: 6px;">Skills Extracted</div>
        <div>${skillsBadges || 'None detected'}</div>
      </div>
      <div style="margin-bottom: 16px;">
        <div style="font-size: 0.8rem; text-transform: uppercase; color: var(--text-dim); font-weight: 700; margin-bottom: 6px;">Tools & Technologies</div>
        <div>${toolsBadges || 'None detected'}</div>
      </div>
      <div style="margin-bottom: 16px;">
        <div style="font-size: 0.8rem; text-transform: uppercase; color: var(--text-dim); font-weight: 700; margin-bottom: 6px;">Experience (${data.total_experience_years} years)</div>
        <div>${expHtml || 'None detected'}</div>
      </div>
      <div style="margin-bottom: 16px;">
        <div style="font-size: 0.8rem; text-transform: uppercase; color: var(--text-dim); font-weight: 700; margin-bottom: 6px;">Education</div>
        <div style="font-size: 0.9rem; color: var(--text-muted);">${eduHtml}</div>
      </div>
      <button class="btn-primary" onclick="switchView('jd')" style="margin-top: 10px;">Proceed to Job Description →</button>
    </div>
  `;
}

function renderJdParsedPreview(data) {
  const container = document.getElementById('jd-parsed-preview');
  if (!container) return;
  container.style.display = 'block';

  let skillsBadges = (data.required_skills || []).map(s => `<span class="skill-badge matched">${s}</span>`).join(' ');

  let respHtml = (data.job_responsibilities || []).map(r => `
    <li style="margin-bottom: 6px; font-size: 0.9rem; color: var(--text-muted);">${r}</li>
  `).join('');

  container.innerHTML = `
    <div style="margin-top: 24px; border-top: 1px solid var(--border-subtle); padding-top: 20px;">
      <h3 style="font-family: var(--font-heading); margin-bottom: 16px; color: var(--primary);">✓ Extracted Target Role: ${data.job_title} (${data.company})</h3>
      <div style="margin-bottom: 16px;">
        <div style="font-size: 0.8rem; text-transform: uppercase; color: var(--text-dim); font-weight: 700; margin-bottom: 6px;">Required Technical Skills</div>
        <div>${skillsBadges}</div>
      </div>
      <div style="margin-bottom: 16px;">
        <div style="font-size: 0.8rem; text-transform: uppercase; color: var(--text-dim); font-weight: 700; margin-bottom: 6px;">Requirements</div>
        <div style="font-size: 0.9rem; color: var(--text-muted);">
          • Experience: <strong>${data.experience_requirements}</strong><br>
          • Education: <strong>${data.education_requirements}</strong>
        </div>
      </div>
      <div style="margin-bottom: 16px;">
        <div style="font-size: 0.8rem; text-transform: uppercase; color: var(--text-dim); font-weight: 700; margin-bottom: 6px;">Key Responsibilities</div>
        <ul style="padding-left: 20px;">${respHtml}</ul>
      </div>
      <button class="btn-primary" onclick="triggerMatchAndCompare()" style="margin-top: 10px;">Run Comparison & Eligibility Engine →</button>
    </div>
  `;
}

// ------------------------------------------
// 1. Dashboard View
// ------------------------------------------
function renderDashboard() {
  const match = State.analysisData?.match_result;
  const resume = State.analysisData?.resume_parsed;
  const jd = State.analysisData?.jd_parsed;

  if (!match) {
    document.getElementById('dash-empty-state').style.display = 'block';
    document.getElementById('dash-content-state').style.display = 'none';
    return;
  }

  document.getElementById('dash-empty-state').style.display = 'none';
  document.getElementById('dash-content-state').style.display = 'block';

  // Animate circular gauge
  const score = match.overall_score || 0;
  const circle = document.getElementById('dash-gauge-bar');
  const number = document.getElementById('dash-gauge-number');
  if (circle && number) {
    number.innerText = score;
    const circumference = 2 * Math.PI * 60; // r=60 => 377
    const offset = circumference - (score / 100) * circumference;
    circle.style.strokeDashoffset = offset;
    
    // Colorize gauge based on score
    if (score >= 75) circle.style.stroke = 'var(--success)';
    else if (score >= 55) circle.style.stroke = 'var(--warning)';
    else circle.style.stroke = 'var(--danger)';
  }

  // Eligibility badge
  const eligBadge = document.getElementById('dash-elig-badge');
  if (eligBadge) {
    eligBadge.innerText = match.eligibility_status;
    eligBadge.className = `eligibility-badge ${match.eligibility_status.toLowerCase().replace(/\s+/g, '-')}`;
  }

  // Stats
  document.getElementById('dash-matched-count').innerText = match.matched_skills.length;
  document.getElementById('dash-missing-count').innerText = match.missing_skills.length;
  
  const interviewScore = State.interviewSession?.average_interview_score || 0;
  document.getElementById('dash-interview-score').innerText = interviewScore > 0 ? `${interviewScore} / 10` : 'Not Started';

  // Candidate and role summary
  document.getElementById('dash-candidate-name').innerText = resume?.candidate_name || 'Candidate';
  document.getElementById('dash-target-role').innerText = `${jd?.job_title || 'Target Role'} at ${jd?.company || 'Company'}`;
}

// ------------------------------------------
// 2. Job Match & Eligibility View
// ------------------------------------------
function renderJobMatchView() {
  const match = State.analysisData?.match_result;
  if (!match) return;

  // Render 5 Pillars
  document.getElementById('pillar-skill-score').innerText = `${match.skill_match_score}%`;
  document.getElementById('pillar-skill-fill').style.width = `${match.skill_match_score}%`;

  document.getElementById('pillar-exp-score').innerText = `${match.experience_match_score}%`;
  document.getElementById('pillar-exp-fill').style.width = `${match.experience_match_score}%`;

  document.getElementById('pillar-edu-score').innerText = `${match.education_match_score}%`;
  document.getElementById('pillar-edu-fill').style.width = `${match.education_match_score}%`;

  document.getElementById('pillar-cert-score').innerText = `${match.certification_match_score}%`;
  document.getElementById('pillar-cert-fill').style.width = `${match.certification_match_score}%`;

  document.getElementById('pillar-resp-score').innerText = `${match.responsibility_match_score}%`;
  document.getElementById('pillar-resp-fill').style.width = `${match.responsibility_match_score}%`;

  // Render Eligibility Banner
  const banner = document.getElementById('match-eligibility-banner');
  const badgeClass = match.eligibility_status.toLowerCase().replace(/\s+/g, '-');
  banner.className = `eligibility-banner ${badgeClass}`;
  banner.innerHTML = `
    <span class="eligibility-badge ${badgeClass}">${match.eligibility_status}</span>
    <div>
      <h4 style="font-family: var(--font-heading); font-size: 1.15rem; color: #fff;">Eligibility Assessment Result</h4>
      <p style="font-size: 0.92rem; color: var(--text-muted); margin-top: 4px;">${match.eligibility_summary}</p>
    </div>
  `;

  // Criteria Table
  const tableBody = document.getElementById('eligibility-checks-tbody');
  tableBody.innerHTML = (match.eligibility_checks || []).map(c => `
    <tr>
      <td><strong>${c.criterion}</strong></td>
      <td>
        <span class="skill-badge ${c.status === 'satisfied' ? 'matched' : (c.status === 'partially_satisfied' ? 'partial' : 'missing')}">
          ${c.status === 'satisfied' ? '✓ Satisfied' : (c.status === 'partially_satisfied' ? '⚠️ Partially Met' : '✗ Not Met')}
        </span>
      </td>
      <td>${c.candidate_value}</td>
      <td>${c.required_value}</td>
      <td style="font-size: 0.85rem; color: var(--text-muted);">${c.explanation}</td>
    </tr>
  `).join('');

  // Strengths & Areas to Improve
  const strengthsList = document.getElementById('match-strengths-list');
  strengthsList.innerHTML = (match.strengths || []).map(s => `<li style="margin-bottom: 8px;">✓ ${s}</li>`).join('');

  const areasList = document.getElementById('match-areas-list');
  areasList.innerHTML = (match.areas_to_improve || []).map(a => `<li style="margin-bottom: 8px;">• ${a}</li>`).join('');
}

// ------------------------------------------
// 3. Skill Gap View
// ------------------------------------------
function renderSkillGapView() {
  const match = State.analysisData?.match_result;
  if (!match) return;

  // Render badge clusters
  const matchedCluster = document.getElementById('gap-matched-badges');
  matchedCluster.innerHTML = (match.matched_skills || []).map(s => `<span class="skill-badge matched">✓ ${s}</span>`).join('');

  const missingCluster = document.getElementById('gap-missing-badges');
  missingCluster.innerHTML = (match.missing_skills || []).map(s => `<span class="skill-badge missing">✗ ${s}</span>`).join('');

  const partialCluster = document.getElementById('gap-partial-badges');
  partialCluster.innerHTML = (match.partially_matched_skills || []).map(p => `<span class="skill-badge partial">≈ ${p.name} (Related: ${p.matched_with || 'Base'})</span>`).join('');

  const recCluster = document.getElementById('gap-recommended-badges');
  recCluster.innerHTML = (match.recommended_skills || []).map(r => `<span class="skill-badge recommended">+ ${r.name}</span>`).join('');

  // Render detailed Missing Skill Cards
  const cardsGrid = document.getElementById('gap-detailed-cards-grid');
  const allDetails = match.all_skill_details.filter(d => d.status === 'missing' || d.status === 'partially_matched');

  cardsGrid.innerHTML = allDetails.map(item => `
    <div class="gap-card">
      <div class="gap-card-header">
        <div class="gap-skill-name">${item.name}</div>
        <span class="priority-tag ${item.estimated_priority.toLowerCase().includes('p1') ? 'p1' : (item.estimated_priority.toLowerCase().includes('p2') ? 'p2' : 'p3')}">
          ${item.estimated_priority}
        </span>
      </div>
      <div>
        <div class="gap-field-label">Why It Is Required</div>
        <div class="gap-field-text">${item.why_required}</div>
      </div>
      <div>
        <div class="gap-field-label">Suggested Learning Direction</div>
        <div class="gap-field-text">${item.suggested_learning_direction}</div>
      </div>
      <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border-subtle); padding-top: 12px; margin-top: 8px;">
        <span style="font-size: 0.8rem; color: var(--text-dim);">Difficulty: <strong>${item.difficulty_level}</strong></span>
        <span style="font-size: 0.8rem; color: var(--primary);">Importance: <strong>${item.importance}</strong></span>
      </div>
    </div>
  `).join('');
}

// ------------------------------------------
// 4. Job Fit Report View
// ------------------------------------------
function renderJobFitReportView() {
  const match = State.analysisData?.match_result;
  const resume = State.analysisData?.resume_parsed;
  const jd = State.analysisData?.jd_parsed;
  if (!match) return;

  document.getElementById('report-candidate-header').innerText = `${resume?.candidate_name || 'Candidate'} - Job Fit Analysis`;
  document.getElementById('report-role-header').innerText = `Role: ${jd?.job_title || 'Position'} | ${jd?.company || 'Employer'}`;
  document.getElementById('report-date').innerText = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });

  // Circular gauge for report
  document.getElementById('report-score-number').innerText = match.overall_score;
  const circle = document.getElementById('report-gauge-bar');
  if (circle) {
    const circumference = 2 * Math.PI * 60;
    circle.style.strokeDashoffset = circumference - (match.overall_score / 100) * circumference;
  }

  // Eligibility
  const eligBadge = document.getElementById('report-elig-badge');
  eligBadge.innerText = match.eligibility_status;
  eligBadge.className = `eligibility-badge ${match.eligibility_status.toLowerCase().replace(/\s+/g, '-')}`;

  // Breakdown scores
  document.getElementById('report-skill-val').innerText = `${match.skill_match_score}%`;
  document.getElementById('report-exp-val').innerText = `${match.experience_match_score}%`;
  document.getElementById('report-edu-val').innerText = `${match.education_match_score}%`;
  document.getElementById('report-cert-val').innerText = `${match.certification_match_score}%`;
  document.getElementById('report-resp-val').innerText = `${match.responsibility_match_score}%`;

  // Matched & Missing Skills
  document.getElementById('report-matched-skills').innerHTML = match.matched_skills.map(s => `<span class="skill-badge matched">${s}</span>`).join(' ');
  document.getElementById('report-missing-skills').innerHTML = match.missing_skills.map(s => `<span class="skill-badge missing">${s}</span>`).join(' ');

  // Strengths & Improvement
  document.getElementById('report-strengths-ul').innerHTML = match.strengths.map(s => `<li>${s}</li>`).join('');
  document.getElementById('report-areas-ul').innerHTML = match.areas_to_improve.map(a => `<li>${a}</li>`).join('');
}

function exportReportPDF() {
  window.print();
}

// ------------------------------------------
// 5. Mock Interview Chamber & Logic
// ------------------------------------------
function initInterviewListeners() {
  const answerTextarea = document.getElementById('interview-answer-input');
  if (answerTextarea) {
    answerTextarea.addEventListener('input', () => {
      const words = answerTextarea.value.trim() ? answerTextarea.value.trim().split(/\s+/).length : 0;
      const counter = document.getElementById('interview-word-count');
      if (counter) counter.innerText = `${words} words`;
    });
  }
}

function startInterviewTimer() {
  clearInterval(State.interviewTimerInterval);
  State.interviewTimeSeconds = 0;
  const timerDisplay = document.getElementById('interview-timer-display');
  State.interviewTimerInterval = setInterval(() => {
    State.interviewTimeSeconds++;
    const mins = String(Math.floor(State.interviewTimeSeconds / 60)).padStart(2, '0');
    const secs = String(State.interviewTimeSeconds % 60).padStart(2, '0');
    if (timerDisplay) timerDisplay.innerText = `${mins}:${secs}`;
  }, 1000);
}

function stopInterviewTimer() {
  clearInterval(State.interviewTimerInterval);
}

function renderMockInterviewChamber() {
  const session = State.interviewSession;
  if (!session || !session.questions || session.questions.length === 0) {
    document.getElementById('interview-empty-state').style.display = 'block';
    document.getElementById('interview-active-state').style.display = 'none';
    return;
  }

  document.getElementById('interview-empty-state').style.display = 'none';
  document.getElementById('interview-active-state').style.display = 'block';

  const idx = State.activeQuestionIndex;
  const total = session.questions.length;
  const q = session.questions[idx];

  // Header & indicators
  document.getElementById('interview-q-counter').innerText = `Question ${idx + 1} of ${total}`;
  document.getElementById('interview-cat-badge').innerText = q.category;
  document.getElementById('interview-question-body').innerText = q.question_text;
  document.getElementById('interview-context-body').innerText = `Context: ${q.context_source}`;

  // Progress track
  const progressPercent = ((idx + 1) / total) * 100;
  document.getElementById('interview-progress-fill').style.width = `${progressPercent}%`;

  // Reset answer input or show past answer if already submitted
  const textarea = document.getElementById('interview-answer-input');
  const pastAnswer = session.answers?.[q.id];
  const evalCard = document.getElementById('interview-evaluation-card');

  if (pastAnswer) {
    textarea.value = pastAnswer.user_answer;
    document.getElementById('interview-word-count').innerText = `${pastAnswer.user_answer.split(/\s+/).length} words`;
    if (pastAnswer.evaluation) {
      renderAnswerEvaluationCard(pastAnswer.evaluation);
    }
  } else {
    textarea.value = '';
    document.getElementById('interview-word-count').innerText = '0 words';
    if (evalCard) evalCard.style.display = 'none';
  }

  startInterviewTimer();
}

async function submitInterviewAnswer() {
  const session = State.interviewSession;
  if (!session) return;
  const q = session.questions[State.activeQuestionIndex];
  const answerText = document.getElementById('interview-answer-input').value.trim();

  if (!answerText) {
    showToast('Please type or dictate your answer before submitting.', 'error');
    return;
  }

  stopInterviewTimer();
  showToast('Evaluating answer with AI rubric...', 'info');

  try {
    const res = await API.submitAnswer(
      session.id,
      q.id,
      answerText,
      State.interviewTimeSeconds
    );

    // Update local state
    if (!State.interviewSession.answers) State.interviewSession.answers = {};
    State.interviewSession.answers[q.id] = {
      question_id: q.id,
      question_category: q.category,
      question_text: q.question_text,
      user_answer: answerText,
      time_spent_seconds: State.interviewTimeSeconds,
      evaluation: res.evaluation
    };
    State.interviewSession.average_interview_score = res.average_score;

    showToast('Evaluation complete!', 'success');
    renderAnswerEvaluationCard(res.evaluation);
  } catch (err) {
    showToast(err.message || 'Evaluation error', 'error');
  }
}

function renderAnswerEvaluationCard(ev) {
  const card = document.getElementById('interview-evaluation-card');
  if (!card) return;
  card.style.display = 'block';

  // Metrics
  document.getElementById('eval-tech-acc').innerText = `${ev.technical_accuracy_score} / 10`;
  document.getElementById('eval-relevance').innerText = `${ev.relevance_score} / 10`;
  document.getElementById('eval-complete').innerText = `${ev.completeness_score} / 10`;
  document.getElementById('eval-comm').innerText = `${ev.communication_score} / 10`;
  document.getElementById('eval-overall').innerText = `${ev.overall_score} / 10`;

  // Feedback Lists
  const wellList = document.getElementById('eval-did-well');
  wellList.innerHTML = (ev.what_you_did_well || []).map(w => `<li>✓ ${w}</li>`).join('');

  const improveList = document.getElementById('eval-can-improve');
  improveList.innerHTML = (ev.what_you_can_improve || []).map(i => `<li>• ${i}</li>`).join('');

  const missingList = document.getElementById('eval-missing-points');
  missingList.innerHTML = (ev.missing_points || []).map(m => `<li>⚠️ ${m}</li>`).join('');

  document.getElementById('eval-model-answer').innerText = ev.better_answer_approach || 'Model answer not available';

  // Scroll down smoothly to feedback
  card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function nextQuestion() {
  const session = State.interviewSession;
  if (!session) return;
  if (State.activeQuestionIndex < session.questions.length - 1) {
    State.activeQuestionIndex++;
    renderMockInterviewChamber();
  } else {
    showToast('All interview questions completed! Navigating to results.', 'success');
    switchView('interview-results');
  }
}

function prevQuestion() {
  if (State.activeQuestionIndex > 0) {
    State.activeQuestionIndex--;
    renderMockInterviewChamber();
  }
}

function skipQuestion() {
  showToast('Question skipped.', 'info');
  nextQuestion();
}

// ------------------------------------------
// 6. Interview Results View
// ------------------------------------------
function renderInterviewResults() {
  const session = State.interviewSession;
  if (!session || !session.answers || Object.keys(session.answers).length === 0) {
    document.getElementById('results-empty-state').style.display = 'block';
    document.getElementById('results-content-state').style.display = 'none';
    return;
  }

  document.getElementById('results-empty-state').style.display = 'none';
  document.getElementById('results-content-state').style.display = 'block';

  document.getElementById('results-avg-score').innerText = `${session.average_interview_score} / 10`;
  document.getElementById('results-answered-count').innerText = `${Object.keys(session.answers).length} of ${session.questions.length}`;

  const listContainer = document.getElementById('results-questions-accordion');
  listContainer.innerHTML = session.questions.map((q, i) => {
    const ans = session.answers[q.id];
    if (!ans) {
      return `
        <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); padding: 18px; margin-bottom: 12px; opacity: 0.6;">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: 600;">Question ${i + 1}: ${q.question_text}</span>
            <span class="skill-badge missing">Skipped</span>
          </div>
        </div>
      `;
    }

    const ev = ans.evaluation || {};
    return `
      <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 24px; margin-bottom: 16px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
          <div>
            <span class="category-pill">${q.category}</span>
            <h4 style="font-family: var(--font-heading); font-size: 1.15rem; color: #fff; margin-top: 8px;">Q${i + 1}: ${q.question_text}</h4>
          </div>
          <span class="skill-badge matched" style="font-size: 1rem;">${ev.overall_score || 0} / 10</span>
        </div>
        
        <div style="background: var(--bg-primary); border-radius: var(--radius-sm); padding: 14px; margin-bottom: 16px; font-size: 0.92rem; color: var(--text-muted);">
          <strong style="color: #fff;">Your Response:</strong><br>
          ${ans.user_answer}
        </div>

        <div class="feedback-grid" style="margin-bottom: 16px;">
          <div class="feedback-metric-box">
            <div class="feedback-metric-val">${ev.technical_accuracy_score || 0}/10</div>
            <div class="feedback-metric-lbl">Tech Accuracy</div>
          </div>
          <div class="feedback-metric-box">
            <div class="feedback-metric-val">${ev.relevance_score || 0}/10</div>
            <div class="feedback-metric-lbl">Relevance</div>
          </div>
          <div class="feedback-metric-box">
            <div class="feedback-metric-val">${ev.completeness_score || 0}/10</div>
            <div class="feedback-metric-lbl">Completeness</div>
          </div>
          <div class="feedback-metric-box">
            <div class="feedback-metric-val">${ev.communication_score || 0}/10</div>
            <div class="feedback-metric-lbl">Communication</div>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 14px;">
          <div>
            <strong style="color: var(--success); font-size: 0.85rem; text-transform: uppercase;">What You Did Well:</strong>
            <ul style="padding-left: 20px; font-size: 0.88rem; color: var(--text-muted); margin-top: 4px;">
              ${(ev.what_you_did_well || []).map(w => `<li>${w}</li>`).join('')}
            </ul>
          </div>
          <div>
            <strong style="color: var(--warning); font-size: 0.85rem; text-transform: uppercase;">What Can Be Improved:</strong>
            <ul style="padding-left: 20px; font-size: 0.88rem; color: var(--text-muted); margin-top: 4px;">
              ${(ev.what_you_can_improve || []).map(imp => `<li>${imp}</li>`).join('')}
            </ul>
          </div>
        </div>

        <details style="margin-top: 12px; cursor: pointer;">
          <summary style="color: var(--primary); font-size: 0.88rem; font-weight: 600;">View Recommended Model Answer</summary>
          <div style="background: rgba(0, 210, 255, 0.05); border-left: 3px solid var(--primary); padding: 12px 16px; margin-top: 8px; font-size: 0.88rem; color: var(--text-main); white-space: pre-line;">
            ${ev.better_answer_approach}
          </div>
        </details>
      </div>
    `;
  }).join('');
}

// ------------------------------------------
// 7. Final Preparation Report View
// ------------------------------------------
async function renderPreparationReport() {
  if (!State.currentAnalysisId) return;
  try {
    const report = await API.getPreparationReport(State.currentAnalysisId);

    document.getElementById('prep-candidate-name').innerText = report.candidate_name;
    document.getElementById('prep-job-title').innerText = report.job_title;
    document.getElementById('prep-match-score').innerText = `${report.overall_match_score}%`;
    document.getElementById('prep-elig-status').innerText = report.eligibility_status;
    document.getElementById('prep-interview-score').innerText = `${report.interview_average_score} / 10`;

    // Recommended topics
    document.getElementById('prep-topics-list').innerHTML = (report.recommended_topics || []).map(t => `
      <li style="margin-bottom: 8px; color: var(--text-main);">
        <strong style="color: var(--primary);">•</strong> ${t}
      </li>
    `).join('');

    // Checklist
    const checklistContainer = document.getElementById('prep-checklist-container');
    checklistContainer.innerHTML = (report.checklist || []).map(c => `
      <div class="checklist-item ${State.checklistState[c.id] ? 'done' : ''}" onclick="toggleChecklistItem('${c.id}')">
        <div class="custom-checkbox">${State.checklistState[c.id] ? '✓' : ''}</div>
        <div>
          <div style="font-weight: 600; color: #fff; font-size: 0.95rem;">${c.title} <span style="font-size: 0.75rem; color: var(--text-dim); margin-left: 6px;">[${c.category}]</span></div>
          <div style="font-size: 0.85rem; color: var(--text-muted); margin-top: 4px;">${c.description}</div>
        </div>
      </div>
    `).join('');
  } catch (err) {
    showToast(err.message || 'Error loading preparation report', 'error');
  }
}

function toggleChecklistItem(id) {
  State.checklistState[id] = !State.checklistState[id];
  renderPreparationReport();
}

// ==========================================
// Speech-to-Text Feature
// ==========================================
function initSpeechRecognition() {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRec) return;

  State.speechRecognition = new SpeechRec();
  State.speechRecognition.continuous = true;
  State.speechRecognition.interimResults = true;

  State.speechRecognition.onresult = (event) => {
    let transcript = '';
    for (let i = event.resultIndex; i < event.results.length; i++) {
      transcript += event.results[i][0].transcript;
    }
    const input = document.getElementById('interview-answer-input');
    if (input) {
      input.value += (input.value ? ' ' : '') + transcript;
      input.dispatchEvent(new Event('input'));
    }
  };

  State.speechRecognition.onerror = (event) => {
    console.warn('Speech recognition error:', event.error);
    stopListening();
  };
}

function toggleSpeechRecognition() {
  if (!State.speechRecognition) {
    showToast('Speech-to-text is not supported by your current browser. You can type your answer directly.', 'info');
    return;
  }
  if (State.isListening) {
    stopListening();
  } else {
    startListening();
  }
}

function startListening() {
  if (!State.speechRecognition) return;
  try {
    State.speechRecognition.start();
    State.isListening = true;
    const btn = document.getElementById('btn-speech-dictate');
    if (btn) {
      btn.classList.add('listening');
      btn.innerHTML = `🔴 Listening... (Click to stop)`;
    }
    showToast('Microphone active. Speak your answer...', 'info');
  } catch (e) {
    console.error(e);
  }
}

function stopListening() {
  if (!State.speechRecognition) return;
  try {
    State.speechRecognition.stop();
    State.isListening = false;
    const btn = document.getElementById('btn-speech-dictate');
    if (btn) {
      btn.classList.remove('listening');
      btn.innerHTML = `🎙️ Dictate Answer (Voice)`;
    }
  } catch (e) {
    console.error(e);
  }
}

// =======================================================
// SUPABASE CLOUD DATABASE CONTROLLERS
// =======================================================

let cachedSupabaseSchema = "";

async function renderSupabaseDashboard() {
  try {
    const status = await API.getSupabaseStatus();
    const urlCard = document.getElementById('sb-card-url');
    if (urlCard && status.url) {
      urlCard.textContent = status.url;
    }

    const alertBox = document.getElementById('sb-tables-alert');
    if (alertBox) {
      if (!status.all_tables_ready) {
        alertBox.style.display = 'block';
      } else {
        alertBox.style.display = 'none';
      }
    }

    // Update counts from status if available
    if (status.tables) {
      const empCountEl = document.getElementById('sb-card-emp-count');
      const qCountEl = document.getElementById('sb-card-q-count');
      const perfCountEl = document.getElementById('sb-card-perf-count');

      if (empCountEl && status.tables.employee_data && status.tables.employee_data.exists) {
        empCountEl.textContent = status.tables.employee_data.count;
      }
      if (qCountEl && status.tables.questions && status.tables.questions.exists) {
        qCountEl.textContent = status.tables.questions.count;
      }
      if (perfCountEl && status.tables.performance_details && status.tables.performance_details.exists) {
        perfCountEl.textContent = status.tables.performance_details.count;
      }
    }

    await loadSupabaseData();
  } catch (e) {
    console.error('Error rendering Supabase dashboard:', e);
  }
}

function switchSupabaseTab(tab) {
  ['emp', 'questions', 'perf'].forEach(t => {
    const btn = document.getElementById(`tab-btn-sb-${t}`);
    const pane = document.getElementById(`sb-tab-pane-${t}`);
    if (btn && pane) {
      if (t === tab) {
        btn.classList.add('active');
        pane.style.display = 'block';
      } else {
        btn.classList.remove('active');
        pane.style.display = 'none';
      }
    }
  });
}

async function loadSupabaseData() {
  // Load Employee Data
  try {
    const empRes = await API.getSupabaseEmployeeData();
    renderEmployeeDataTable(empRes.records || []);
    const empCountEl = document.getElementById('sb-card-emp-count');
    if (empCountEl && empRes.records) empCountEl.textContent = empRes.records.length;
  } catch (e) {
    console.warn('Error loading Supabase employee data:', e);
  }

  // Load Questions
  try {
    const qRes = await API.getSupabaseQuestions();
    renderQuestionsList(qRes.records || []);
    const qCountEl = document.getElementById('sb-card-q-count');
    if (qCountEl && qRes.records) qCountEl.textContent = qRes.records.length;
  } catch (e) {
    console.warn('Error loading Supabase questions:', e);
  }

  // Load Performance Details
  try {
    const perfRes = await API.getSupabasePerformance();
    renderPerformanceDetailsList(perfRes.records || []);
    const perfCountEl = document.getElementById('sb-card-perf-count');
    if (perfCountEl && perfRes.records) perfCountEl.textContent = perfRes.records.length;
  } catch (e) {
    console.warn('Error loading Supabase performance:', e);
  }
}

function renderEmployeeDataTable(records) {
  const container = document.getElementById('sb-emp-table-container');
  if (!container) return;

  if (!records || records.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 40px; background: rgba(255,255,255,0.02); border-radius: var(--radius-sm); border: 1px dashed var(--border-subtle);">
        <div style="font-size: 2rem; margin-bottom: 8px;">📂</div>
        <div style="font-weight: 600; color: #fff; margin-bottom: 4px;">No Candidate Records Found in Supabase Yet</div>
        <p style="font-size: 0.85rem; color: var(--text-dim); max-width: 480px; margin: 0 auto 16px auto;">
          Upload a resume or click "Sync All Local Data to Supabase" above to push candidates into cloud storage.
        </p>
        <button class="btn-primary" onclick="syncAllToSupabaseAction()" style="font-size: 0.82rem; padding: 6px 16px;">
          ⚡ Sync Local Data Now
        </button>
      </div>
    `;
    return;
  }

  let html = `
    <table class="data-table" style="width: 100%; border-collapse: collapse; font-size: 0.88rem;">
      <thead>
        <tr style="border-bottom: 1px solid var(--border-subtle); color: var(--text-muted); text-align: left;">
          <th style="padding: 12px 14px;">Candidate Name</th>
          <th style="padding: 12px 14px;">Target Position</th>
          <th style="padding: 12px 14px;">Contact Info</th>
          <th style="padding: 12px 14px;">Resume File</th>
          <th style="padding: 12px 14px;">Parsed Skills</th>
          <th style="padding: 12px 14px;">Synced At</th>
        </tr>
      </thead>
      <tbody>
  `;

  records.forEach(r => {
    const parsed = r.resume_parsed || {};
    const skillsList = parsed.skills || parsed.tools_and_technologies || [];
    const skillsCount = skillsList.length;
    const dateStr = r.created_at ? new Date(r.created_at).toLocaleDateString() : 'Recent';

    html += `
      <tr style="border-bottom: 1px solid rgba(255,255,255,0.04);">
        <td style="padding: 12px 14px; font-weight: 600; color: #fff;">${escapeHtml(r.candidate_name || 'Candidate')}</td>
        <td style="padding: 12px 14px; color: var(--primary);">${escapeHtml(r.job_title || 'Position')}</td>
        <td style="padding: 12px 14px; color: var(--text-muted); font-size: 0.82rem;">${escapeHtml(r.email || r.phone || 'N/A')}</td>
        <td style="padding: 12px 14px; color: var(--text-dim); font-size: 0.82rem;">${escapeHtml(r.resume_filename || 'Text')}</td>
        <td style="padding: 12px 14px;"><span class="badge" style="background: rgba(0, 210, 255, 0.15); color: var(--primary);">${skillsCount} Skills</span></td>
        <td style="padding: 12px 14px; color: var(--text-dim); font-size: 0.8rem;">${dateStr}</td>
      </tr>
    `;
  });

  html += `</tbody></table>`;
  container.innerHTML = html;
}

function renderQuestionsList(records) {
  const container = document.getElementById('sb-questions-container');
  if (!container) return;

  if (!records || records.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 40px; background: rgba(255,255,255,0.02); border-radius: var(--radius-sm); border: 1px dashed var(--border-subtle);">
        <div style="font-size: 2rem; margin-bottom: 8px;">❓</div>
        <div style="font-weight: 600; color: #fff; margin-bottom: 4px;">No Questions Found in Supabase Yet</div>
        <p style="font-size: 0.85rem; color: var(--text-dim); max-width: 480px; margin: 0 auto 16px auto;">
          Generate interview questions or load the demo to push questions into cloud storage.
        </p>
        <button class="btn-primary" onclick="syncAllToSupabaseAction()" style="font-size: 0.82rem; padding: 6px 16px;">
          ⚡ Sync Local Questions Now
        </button>
      </div>
    `;
    return;
  }

  let html = `<div style="display: flex; flex-direction: column; gap: 12px;">`;

  records.forEach((q, idx) => {
    const catColors = {
      'HR': 'rgba(59, 130, 246, 0.15); color: #60a5fa;',
      'Technical': 'rgba(16, 185, 129, 0.15); color: #34d399;',
      'Behavioral': 'rgba(245, 158, 11, 0.15); color: #fbbf24;',
      'Resume-Based': 'rgba(139, 92, 246, 0.15); color: #a78bfa;',
      'JD-Specific': 'rgba(236, 72, 153, 0.15); color: #f472b6;'
    };
    const styleBadge = catColors[q.category] || 'rgba(255, 255, 255, 0.1); color: #fff;';

    html += `
      <div style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); padding: 16px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
          <span style="font-size: 0.78rem; font-weight: 600; padding: 3px 10px; border-radius: var(--radius-full); background: ${styleBadge}">
            ${escapeHtml(q.category || 'General')}
          </span>
          <span style="font-size: 0.78rem; color: var(--text-dim);">Q#${idx + 1}</span>
        </div>
        <div style="font-size: 0.95rem; font-weight: 500; color: #fff; margin-bottom: 6px;">
          ${escapeHtml(q.question_text || '')}
        </div>
        ${q.context_source ? `<div style="font-size: 0.82rem; color: var(--text-muted); font-style: italic;">Rationale: ${escapeHtml(q.context_source)}</div>` : ''}
      </div>
    `;
  });

  html += `</div>`;
  container.innerHTML = html;
}

function renderPerformanceDetailsList(records) {
  const container = document.getElementById('sb-perf-container');
  if (!container) return;

  if (!records || records.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 40px; background: rgba(255,255,255,0.02); border-radius: var(--radius-sm); border: 1px dashed var(--border-subtle);">
        <div style="font-size: 2rem; margin-bottom: 8px;">📊</div>
        <div style="font-weight: 600; color: #fff; margin-bottom: 4px;">No Performance Records Found in Supabase Yet</div>
        <p style="font-size: 0.85rem; color: var(--text-dim); max-width: 480px; margin: 0 auto 16px auto;">
          Complete an algorithmic match or mock interview to automatically save candidate performance details.
        </p>
        <button class="btn-primary" onclick="syncAllToSupabaseAction()" style="font-size: 0.82rem; padding: 6px 16px;">
          ⚡ Sync Local Performance Data
        </button>
      </div>
    `;
    return;
  }

  let html = `<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px;">`;

  records.forEach(p => {
    const eligStatus = p.eligibility_status || 'Pending';
    const statusColor = eligStatus === 'Eligible' ? 'var(--success)' : (eligStatus === 'Partially Eligible' ? 'var(--warning)' : 'var(--danger)');
    const answersCount = p.answers_evaluations ? Object.keys(p.answers_evaluations).length : 0;

    html += `
      <div style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
          <div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #fff; font-family: var(--font-heading);">${escapeHtml(p.candidate_name || 'Candidate')}</div>
            <div style="font-size: 0.85rem; color: var(--primary);">${escapeHtml(p.job_title || 'Role')}</div>
          </div>
          <span style="font-size: 0.78rem; font-weight: 600; padding: 3px 10px; border-radius: var(--radius-full); background: rgba(255,255,255,0.05); color: ${statusColor}; border: 1px solid ${statusColor};">
            ${escapeHtml(eligStatus)}
          </span>
        </div>

        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 16px; background: rgba(0,0,0,0.25); border-radius: var(--radius-sm); padding: 12px; text-align: center;">
          <div>
            <div style="font-size: 0.72rem; color: var(--text-dim); text-transform: uppercase;">Match Score</div>
            <div style="font-size: 1.25rem; font-weight: 700; color: var(--primary);">${Math.round(p.overall_match_score || 0)}%</div>
          </div>
          <div>
            <div style="font-size: 0.72rem; color: var(--text-dim); text-transform: uppercase;">Skill Score</div>
            <div style="font-size: 1.25rem; font-weight: 700; color: var(--secondary);">${Math.round(p.skill_match_score || 0)}%</div>
          </div>
          <div>
            <div style="font-size: 0.72rem; color: var(--text-dim); text-transform: uppercase;">Interview Avg</div>
            <div style="font-size: 1.25rem; font-weight: 700; color: var(--accent-purple);">${p.average_interview_score ? p.average_interview_score.toFixed(1) : '0.0'}/10</div>
          </div>
        </div>

        <div style="font-size: 0.82rem; color: var(--text-muted); display: flex; justify-content: space-between; align-items: center;">
          <span>Answers Evaluated: <strong style="color: #fff;">${answersCount}</strong></span>
          <span>Matched Skills: <strong style="color: var(--success);">${(p.matched_skills || []).length}</strong></span>
        </div>
      </div>
    `;
  });

  html += `</div>`;
  container.innerHTML = html;
}

async function syncAllToSupabaseAction() {
  const btn = document.getElementById('btn-supabase-sync');
  if (btn) btn.textContent = 'Syncing to Supabase...';
  try {
    const res = await API.syncAllToSupabase();
    showToast(`Synced ${res.synced_employees} candidates, ${res.synced_questions} questions, ${res.synced_performance_records} performance records to Supabase!`, 'success');
    await renderSupabaseDashboard();
  } catch (e) {
    showToast('Sync error: ' + e.message, 'error');
  } finally {
    if (btn) btn.textContent = '⚡ Sync All Local Data to Supabase';
  }
}

async function toggleSchemaModal(show) {
  const modal = document.getElementById('sb-schema-modal');
  if (!modal) return;
  if (show) {
    modal.style.display = 'flex';
    if (!cachedSupabaseSchema) {
      try {
        const res = await API.getSupabaseSchema();
        cachedSupabaseSchema = res.schema_sql || "";
      } catch (e) {
        cachedSupabaseSchema = "-- Could not load schema from server";
      }
    }
    const codeEl = document.getElementById('sb-schema-code');
    if (codeEl) codeEl.textContent = cachedSupabaseSchema;
  } else {
    modal.style.display = 'none';
  }
}

function copySqlSchemaToClipboard() {
  const codeEl = document.getElementById('sb-schema-code');
  const text = codeEl && codeEl.textContent ? codeEl.textContent : cachedSupabaseSchema;
  if (!text) {
    API.getSupabaseSchema().then(res => {
      navigator.clipboard.writeText(res.schema_sql);
      showToast('SQL Schema copied to clipboard!', 'success');
    });
    return;
  }
  navigator.clipboard.writeText(text).then(() => {
    showToast('SQL Schema copied to clipboard! Paste it into Supabase SQL editor.', 'success');
  }).catch(() => {
    showToast('Failed to copy. Please select and copy manually.', 'error');
  });
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

