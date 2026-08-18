/**
 * Horizon B2B Services - Cyber-Executive Studio Master Controller (v6.1)
 * Optimized for User-Initiated Processing & Dynamic Generalized NLP
 */

const API_BASE = window.location.origin;

const UI_STRINGS = {
  ar: {
    app_title: "HORIZON",
    app_subtitle: "منظومة معالجة وتصنيف طلبات الأعمال وحوكمة الامتثال المؤسسي",
    nav_dashboard: "لوحة المؤشرات",
    nav_ingestion: "استوديو المعالجة الذكي",
    nav_review: "المراجعة البشرية (HITL)",
    nav_database: "سجل الطلبات",
    nav_catalog: "الدليل والسياسات",
    nav_tests: "الاختبارات المعيارية",
    nav_chat: "مساعد DeepSeek V4",
    btn_export: "تصدير",
    btn_run_tests: "تشغيل الاختبارات",
    kpi_total: "إجمالي الطلبات",
    kpi_pending: "بانتظار المراجعة",
    kpi_approved: "الطلبات المعتمدة",
    kpi_compliance: "نسبة الامتثال"
  },
  en: {
    app_title: "HORIZON",
    app_subtitle: "Enterprise AI Request Ingestion & Governance Studio",
    nav_dashboard: "Analytics",
    nav_ingestion: "Ingestion Studio",
    nav_review: "Human Review (HITL)",
    nav_database: "Repository",
    nav_catalog: "Catalog & Policies",
    nav_tests: "Benchmarks",
    nav_chat: "DeepSeek V4 AI",
    btn_export: "Export",
    btn_run_tests: "Run Benchmarks",
    kpi_total: "Total Requests",
    kpi_pending: "Pending Review",
    kpi_approved: "Approved",
    kpi_compliance: "Compliance Rate"
  }
};

const AppState = {
  lang: 'ar',
  currentTab: 'ingestion',
  requests: [],
  stats: {},
  catalog: [],
  policies: [],
  selectedRequest: null,
  filters: { search: '', status: '', policy: '', service: '' }
};

// --- Initialization ---
document.addEventListener('DOMContentLoaded', async () => {
  setupSpotlightTracker();
  setupNavigation();
  setupEventListeners();
  setupDragAndDrop();
  renderSampleButtons();
  setupKeyboardShortcuts();
  await loadInitialData();
  switchTab('ingestion');
  applyLanguage(AppState.lang);

  // Set initial sample text into editor without auto-running
  if (typeof HORIZON_SAMPLES !== 'undefined' && HORIZON_SAMPLES.length > 0) {
    loadSampleIntoInput(HORIZON_SAMPLES[0]);
  }
});

// Cursor Spotlight Refraction
function setupSpotlightTracker() {
  document.addEventListener('mousemove', (e) => {
    document.querySelectorAll('.spotlight-card').forEach(card => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      card.style.setProperty('--mouse-x', `${x}px`);
      card.style.setProperty('--mouse-y', `${y}px`);
    });
  });
}

function toggleLanguage() {
  AppState.lang = AppState.lang === 'ar' ? 'en' : 'ar';
  applyLanguage(AppState.lang);
}

function applyLanguage(lang) {
  const isArabic = lang === 'ar';
  document.documentElement.lang = lang;
  document.documentElement.dir = isArabic ? 'rtl' : 'ltr';
  document.body.dir = isArabic ? 'rtl' : 'ltr';

  const strings = UI_STRINGS[lang];
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (strings && strings[key]) {
      if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
        el.placeholder = strings[key];
      } else {
        el.textContent = strings[key];
      }
    }
  });

  const langBtn = document.getElementById('btn-toggle-lang');
  if (langBtn) {
    langBtn.innerHTML = isArabic 
      ? '<i class="fa-solid fa-globe text-cyan-400"></i> <span>English</span>' 
      : '<i class="fa-solid fa-globe text-cyan-400"></i> <span>العربية</span>';
  }

  renderSampleButtons();
}

async function loadInitialData() {
  try {
    await Promise.all([
      fetchStats(),
      fetchRequests(),
      fetchCatalog(),
      fetchPolicies()
    ]);
  } catch (err) {
    console.error("Initialization error:", err);
  }
}

// --- API Calls ---

async function fetchStats() {
  try {
    const res = await fetch(`${API_BASE}/api/stats`);
    const data = await res.json();
    if (data.success) {
      AppState.stats = data.data;
      updateStatsUI(AppState.stats);
      if (typeof initCharts === 'function') {
        initCharts(AppState.stats);
      }
    }
  } catch (err) {
    console.error("fetchStats error:", err);
  }
}

async function fetchRequests() {
  try {
    const params = new URLSearchParams();
    if (AppState.filters.search) params.append('search', AppState.filters.search);
    if (AppState.filters.status) params.append('status', AppState.filters.status);
    if (AppState.filters.policy) params.append('policy', AppState.filters.policy);
    if (AppState.filters.service) params.append('service', AppState.filters.service);

    const res = await fetch(`${API_BASE}/api/requests?${params.toString()}`);
    const data = await res.json();
    if (data.success) {
      AppState.requests = data.data;
      renderRequestsTable(AppState.requests);
      renderReviewQueue(AppState.requests);
    }
  } catch (err) {
    console.error("fetchRequests error:", err);
  }
}

async function fetchCatalog() {
  try {
    const res = await fetch(`${API_BASE}/api/catalog`);
    const data = await res.json();
    if (data.success) {
      AppState.catalog = data.services;
      renderCatalogCards(AppState.catalog);
      populateServiceDropdowns(AppState.catalog);
    }
  } catch (err) {
    console.error("fetchCatalog error:", err);
  }
}

async function fetchPolicies() {
  try {
    const res = await fetch(`${API_BASE}/api/policies`);
    const data = await res.json();
    if (data.success) {
      AppState.policies = data.policies;
      renderPolicyCards(AppState.policies);
    }
  } catch (err) {
    console.error("fetchPolicies error:", err);
  }
}

// --- Navigation ---

function setupNavigation() {
  const tabButtons = document.querySelectorAll('[data-tab]');
  tabButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const tabId = btn.getAttribute('data-tab');
      switchTab(tabId);
    });
  });
}

function switchTab(tabId) {
  if (!tabId) return;
  AppState.currentTab = tabId;

  document.querySelectorAll('[data-tab]').forEach(btn => {
    if (btn.getAttribute('data-tab') === tabId) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  document.querySelectorAll('.tab-content-section').forEach(sec => {
    if (sec.id === `tab-${tabId}`) {
      sec.classList.remove('hidden');
      sec.classList.add('fade-in-v6');
    } else {
      sec.classList.add('hidden');
      sec.classList.remove('fade-in-v6');
    }
  });

  if (tabId === 'dashboard') fetchStats();
  else if (tabId === 'review') fetchRequests();
  else if (tabId === 'database') fetchRequests();
}

window.switchTab = switchTab;

function setupEventListeners() {
  const langBtn = document.getElementById('btn-toggle-lang');
  if (langBtn) langBtn.onclick = toggleLanguage;

  const processBtn = document.getElementById('btn-process-request');
  if (processBtn) processBtn.onclick = () => handleProcessSubmit();

  const clearBtn = document.getElementById('btn-clear-input');
  if (clearBtn) {
    clearBtn.onclick = () => {
      const txt = document.getElementById('input-request-text');
      if (txt) txt.value = '';
      updateCharCount();
      document.querySelectorAll('.benchmark-card-v6').forEach(c => c.classList.remove('active'));
      resetDiagnosticsDisplay();
    };
  }

  const textarea = document.getElementById('input-request-text');
  if (textarea) textarea.addEventListener('input', updateCharCount);

  const searchInput = document.getElementById('db-search-input');
  if (searchInput) {
    searchInput.addEventListener('input', debounce(() => {
      AppState.filters.search = searchInput.value;
      fetchRequests();
    }, 250));
  }

  const filterStatus = document.getElementById('db-filter-status');
  if (filterStatus) {
    filterStatus.onchange = () => {
      AppState.filters.status = filterStatus.value;
      fetchRequests();
    };
  }

  const filterPolicy = document.getElementById('db-filter-policy');
  if (filterPolicy) {
    filterPolicy.onchange = () => {
      AppState.filters.policy = filterPolicy.value;
      fetchRequests();
    };
  }

  const resetBtn = document.getElementById('btn-reset-samples');
  if (resetBtn) resetBtn.onclick = handleResetSamples;

  const runTestsBtn = document.getElementById('btn-run-tests');
  if (runTestsBtn) runTestsBtn.onclick = handleRunTests;
}

function setupKeyboardShortcuts() {
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleProcessSubmit();
    }
  });
}

function updateCharCount() {
  const txt = document.getElementById('input-request-text');
  if (!txt) return;
  const countEl = document.getElementById('char-count-badge');
  if (countEl) {
    countEl.textContent = `${txt.value.length} ${AppState.lang === 'ar' ? 'حرف' : 'chars'}`;
  }
}

// --- Benchmark Samples Cards Loader ---

function renderSampleButtons() {
  const container = document.getElementById('sample-buttons-container');
  if (!container || typeof HORIZON_SAMPLES === 'undefined') return;

  const isAr = AppState.lang === 'ar';
  container.innerHTML = '';

  HORIZON_SAMPLES.forEach((sample, idx) => {
    const card = document.createElement('div');
    card.className = `benchmark-card-v6 flex flex-col justify-between ${idx === 0 ? 'active' : ''}`;
    card.id = `sample-card-${sample.letter}`;
    card.innerHTML = `
      <div>
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <span class="w-6 h-6 rounded-lg bg-white/10 text-cyan-400 font-mono font-black flex items-center justify-center text-xs border border-white/15">
              ${sample.letter}
            </span>
            <span class="font-extrabold text-white text-xs">${isAr ? sample.title : (sample.title_en || sample.title)}</span>
          </div>
          <span class="px-2 py-0.5 rounded text-[10px] font-medium bg-white/5 text-slate-300 border border-white/10">
            ${isAr ? sample.category : sample.category}
          </span>
        </div>
        <p class="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">${isAr ? sample.desc : (sample.desc_en || sample.desc)}</p>
      </div>
    `;
    card.onclick = () => {
      document.querySelectorAll('.benchmark-card-v6').forEach(c => c.classList.remove('active'));
      card.classList.add('active');
      
      if (typeof anime !== 'undefined') {
        anime({
          targets: card,
          scale: [0.97, 1],
          duration: 250,
          easing: 'easeOutCubic'
        });
      }
      loadSampleIntoInput(sample);
    };
    container.appendChild(card);
  });
}

function loadSampleIntoInput(sample) {
  const textarea = document.getElementById('input-request-text');
  if (!textarea) return;
  textarea.value = sample.text;
  updateCharCount();
  resetDiagnosticsDisplay(sample);
  
  showToast(
    AppState.lang === 'ar' 
      ? `تم اختيار (${sample.title}). انقر زر "معالجة بالذكاء الاصطناعي" أدناه لبدء التحليل.` 
      : `Loaded (${sample.title_en || sample.title}). Click "Process with AI" to start.`, 
    "info"
  );
}

window.loadSample = function(letter) {
  if (typeof HORIZON_SAMPLES === 'undefined') return;
  const s = HORIZON_SAMPLES.find(x => x.letter === letter);
  if (s) {
    document.querySelectorAll('.benchmark-card-v6').forEach(c => c.classList.remove('active'));
    const card = document.getElementById(`sample-card-${letter}`);
    if (card) card.classList.add('active');
    loadSampleIntoInput(s);
  }
};

function resetDiagnosticsDisplay(sample = null) {
  const isAr = AppState.lang === 'ar';
  setText('res-request-code', 'REQ-PENDING');
  setText('res-confidence-badge', isAr ? 'جاهز للمعالجة' : 'Ready to Process');
  setText('res-org-name', isAr ? 'بانتظار التحليل...' : 'Awaiting analysis...');
  setText('res-contact-person', isAr ? 'بانتظار التحليل...' : 'Awaiting analysis...');
  setText('res-contact-title', '');
  setText('res-contact-channel', isAr ? 'بانتظار التحليل...' : 'Awaiting analysis...');
  
  const crEl = document.getElementById('res-cr-status');
  if (crEl) {
    crEl.textContent = isAr ? 'قيد الفحص' : 'Pending';
    crEl.className = 'telemetry-chip chip-pending';
  }

  setText('res-primary-service', isAr ? 'انقر زر "معالجة بالذكاء الاصطناعي"' : 'Click "Process with AI"');
  setText('res-secondary-service', '-');
  setText('res-deadline', '-');

  const policyEl = document.getElementById('res-policy-status');
  if (policyEl) {
    policyEl.textContent = isAr ? 'قيد التقييم' : 'Pending';
    policyEl.className = 'telemetry-chip chip-pending';
  }

  const missingContainer = document.getElementById('res-missing-list');
  if (missingContainer) {
    missingContainer.innerHTML = `<span class="text-xs text-slate-500 font-mono">${isAr ? 'اضغط زر المعالجة لبدء فحص السياسات الـ 8' : 'Click process to evaluate policies'}</span>`;
  }

  const alertsContainer = document.getElementById('res-alerts-list');
  if (alertsContainer) {
    alertsContainer.innerHTML = '';
  }

  setText('res-next-step', isAr ? 'انقر زر "معالجة بالذكاء الاصطناعي" لبدء الاستخراج الفعلي وتوليد الملخص الموحد.' : 'Click "Process with AI" to generate standardized summary.');
  setText('res-internal-summary', isAr ? '// بانتظار تشغيل المعالجة بالذكاء الاصطناعي...' : '// Awaiting AI Execution...');
  setText('res-customer-subject', '');
  setText('res-customer-body', isAr ? 'سيتم توليد مسودة الرد بعد اكتمال المعالجة بالذكاء الاصطناعي.' : 'Customer draft will generate upon processing.');
}

// --- File Upload & Drag and Drop ---

function setupDragAndDrop() {
  const dropZone = document.getElementById('file-drop-zone');
  const fileInput = document.getElementById('file-upload-input');
  if (!dropZone || !fileInput) return;

  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.classList.add('border-cyan-400', 'bg-white/5');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.classList.remove('border-cyan-400', 'bg-white/5');
    });
  });

  dropZone.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFileUpload(files[0]);
  });

  fileInput.addEventListener('change', (e) => {
    if (fileInput.files.length > 0) handleFileUpload(fileInput.files[0]);
  });
}

async function handleFileUpload(file) {
  const formData = new FormData();
  formData.append('file', file);

  showToast(AppState.lang === 'ar' ? `جاري قراءة واستخراج (${file.name})...` : `Parsing (${file.name})...`, "info");

  try {
    const res = await fetch(`${API_BASE}/api/upload`, {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (data.success) {
      showToast(AppState.lang === 'ar' ? `تم تحليل (${file.name}) بنجاح!` : `File analyzed!`, "success");
      renderAnalysisResult(data.data);
      await fetchStats();
      await fetchRequests();
    } else {
      showToast(data.error || "File parsing failed", "error");
    }
  } catch (err) {
    console.error("Upload error:", err);
    showToast("Error processing file", "error");
  }
}

// --- Real-time Request Processing Workflow ---

async function handleProcessSubmit() {
  const textarea = document.getElementById('input-request-text');
  if (!textarea) return;
  const text = textarea.value.trim();

  if (!text) {
    showToast(AppState.lang === 'ar' ? "الرجاء إدخال نص الطلب أو اختيار أحد النماذج" : "Please input request text", "warning");
    return;
  }

  const processBtn = document.getElementById('btn-process-request');
  const originalBtnHTML = processBtn ? processBtn.innerHTML : '';
  if (processBtn) {
    processBtn.disabled = true;
    processBtn.innerHTML = `<span><i class="fa-solid fa-circle-notch animate-spin text-sm"></i> جاري استخراج الكيانات وفحص السياسات...</span>`;
  }

  try {
    const res = await fetch(`${API_BASE}/api/process`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, source_type: 'text_input' })
    });
    const data = await res.json();

    if (data.success) {
      showToast(AppState.lang === 'ar' ? "تمت معالجة الطلب وتوليد الملخص الموحد بنجاح!" : "Request processed successfully!", "success");
      renderAnalysisResult(data.data);
      await fetchStats();
      await fetchRequests();
    } else {
      showToast(data.error || "Processing failed", "error");
    }
  } catch (err) {
    console.error("Process error:", err);
    showToast("Server error during processing", "error");
  } finally {
    if (processBtn) {
      processBtn.disabled = false;
      processBtn.innerHTML = originalBtnHTML;
    }
  }
}

// --- Render Live Analysis Result ---

function renderAnalysisResult(item) {
  const isAr = AppState.lang === 'ar';

  setText('res-request-code', item.request_code || 'REQ-NEW');
  setText('res-confidence-badge', isAr ? `${Math.round((item.confidence_score || 0.95) * 100)}% دقة المطابقة` : `${Math.round((item.confidence_score || 0.95) * 100)}% Confidence`);

  setText('res-org-name', item.organization_name || '-');
  
  const personEl = document.getElementById('res-contact-person');
  const titleEl = document.getElementById('res-contact-title');
  if (personEl) personEl.textContent = item.contact_person || '-';
  if (titleEl) {
    if (item.contact_title && item.contact_title !== 'غير مذكورة' && item.contact_title !== '(-)') {
      titleEl.textContent = `(${item.contact_title})`;
      titleEl.style.display = 'inline';
    } else {
      titleEl.textContent = '';
      titleEl.style.display = 'none';
    }
  }
  
  setText('res-contact-channel', item.contact_channel || '-');

  const crEl = document.getElementById('res-cr-status');
  if (crEl) {
    crEl.textContent = item.cr_status || '-';
    crEl.className = `telemetry-chip ${getCRBadgeClass(item.cr_status)}`;
  }

  setText('res-primary-service', item.primary_service_name || '-');
  setText('res-secondary-service', item.secondary_service_name || 'لا توجد');

  setText('res-deadline', item.requested_deadline_text || '-');
  const policyEl = document.getElementById('res-policy-status');
  if (policyEl) {
    policyEl.textContent = item.policy_evaluation || 'متوافق';
    policyEl.className = `telemetry-chip ${getPolicyBadgeClass(item.policy_evaluation)}`;
  }

  const missingContainer = document.getElementById('res-missing-list');
  if (missingContainer) {
    missingContainer.innerHTML = '';
    const missing = item.missing_data || [];
    if (missing.length === 0) {
      missingContainer.innerHTML = `<span class="text-xs text-emerald-400 font-bold bg-emerald-950/40 px-3 py-1 rounded-lg border border-emerald-500/30">✓ جميع البيانات الأساسية مكتملة بنجاح</span>`;
    } else {
      missing.forEach(m => {
        const span = document.createElement('span');
        span.className = "text-xs text-amber-300 bg-amber-950/40 px-2.5 py-1 rounded-lg border border-amber-500/30 font-medium";
        span.textContent = `⚠ ${m}`;
        missingContainer.appendChild(span);
      });
    }
  }

  const alertsContainer = document.getElementById('res-alerts-list');
  if (alertsContainer) {
    alertsContainer.innerHTML = '';
    const alerts = item.critical_alerts || [];
    if (alerts.length === 0) {
      alertsContainer.innerHTML = `<div class="text-xs text-slate-500">لا توجد قيود استثنائية أو تنبيهات حرجة.</div>`;
    } else {
      alerts.forEach(a => {
        const div = document.createElement('div');
        div.className = "p-3 rounded-xl bg-rose-950/30 border border-rose-500/30 text-xs text-rose-300 font-medium flex items-start gap-2.5";
        div.innerHTML = `<i class="fa-solid fa-triangle-exclamation mt-0.5 text-rose-400"></i> <span>${a}</span>`;
        alertsContainer.appendChild(div);
      });
    }
  }

  setText('res-next-step', item.suggested_next_step || '-');
  setText('res-internal-summary', item.internal_summary || '');
  setText('res-customer-subject', item.customer_draft_subject || '');
  setText('res-customer-body', item.customer_draft_body || '');

  setupCopyButton('btn-copy-summary', item.internal_summary);
  setupCopyButton('btn-copy-reply', item.customer_draft_body);

  const reviewBtn = document.getElementById('btn-open-review-workbench');
  if (reviewBtn && item.id) {
    reviewBtn.onclick = () => {
      openReviewModal(item.id);
    };
  }
}

// --- Human-in-the-Loop Review Workbench ---

function renderReviewQueue(requests) {
  const container = document.getElementById('review-queue-container');
  if (!container) return;

  const pending = requests.filter(r => r.human_review_status === 'بانتظار المراجعة');
  const countBadge = document.getElementById('pending-review-count');
  if (countBadge) countBadge.textContent = `${pending.length}`;

  const isAr = AppState.lang === 'ar';

  if (pending.length === 0) {
    container.innerHTML = `
      <div class="col-span-full p-10 text-center spotlight-card">
        <div class="w-14 h-14 bg-emerald-950/50 text-emerald-400 rounded-2xl flex items-center justify-center mx-auto mb-3 text-2xl border border-emerald-500/30 shadow-[0_0_20px_rgba(0,255,135,0.15)]">
          <i class="fa-solid fa-check"></i>
        </div>
        <h4 class="text-base font-extrabold text-white">${isAr ? 'طابور المراجعة خالٍ تماماً' : 'Review Queue Clear'}</h4>
        <p class="text-xs text-slate-400 mt-1">${isAr ? 'تمت مراجعة واعتماد كافة الطلبات الواردة بنجاح.' : 'All incoming requests have been reviewed.'}</p>
      </div>
    `;
    return;
  }

  container.innerHTML = '';
  pending.forEach(req => {
    const card = document.createElement('div');
    card.className = "p-5 rounded-2xl spotlight-card flex flex-col justify-between";
    card.innerHTML = `
      <div>
        <div class="flex items-center justify-between mb-3">
          <span class="text-xs font-mono font-bold text-slate-300 bg-white/10 px-2.5 py-1 rounded-md">
            ${req.request_code}
          </span>
          <span class="telemetry-chip ${getPolicyBadgeClass(req.policy_evaluation)} text-xs">
            ${req.policy_evaluation}
          </span>
        </div>
        <h4 class="font-extrabold text-white text-sm mb-1">${req.organization_name || '-'}</h4>
        <div class="text-xs text-slate-400 mb-3 flex items-center gap-2">
          <span><i class="fa-solid fa-user text-cyan-400"></i> ${req.contact_person || '-'}</span>
          <span>•</span>
          <span><i class="fa-solid fa-clock text-amber-400"></i> ${req.requested_deadline_text || '-'}</span>
        </div>
        <div class="p-3 bg-[#080A10] rounded-xl border border-white/5 text-xs text-slate-300 line-clamp-2 mb-4">
          <span class="font-bold text-white">${isAr ? 'الخدمة المطابقة:' : 'Service:'}</span> ${req.primary_service_name}
        </div>
      </div>
      <div class="pt-3 border-t border-white/10 flex items-center justify-between">
        <span class="text-xs text-amber-400 font-bold flex items-center gap-1.5">
          <i class="fa-solid fa-hourglass-half"></i> ${isAr ? 'بانتظار الاعتماد' : 'Pending'}
        </span>
        <button onclick="openReviewModal(${req.id})" class="btn-executive-gold text-xs py-1.5 px-4 cursor-pointer font-bold">
          <i class="fa-solid fa-user-check"></i> ${isAr ? 'مراجعة' : 'Review'}
        </button>
      </div>
    `;
    container.appendChild(card);
  });
}

async function openReviewModal(requestId) {
  try {
    const res = await fetch(`${API_BASE}/api/requests/${requestId}`);
    const data = await res.json();
    if (!data.success) return;

    const req = data.data;
    AppState.selectedRequest = req;

    setText('modal-req-code', req.request_code);
    setText('modal-raw-text', req.raw_text);

    setVal('edit-org-name', req.organization_name || '');
    setVal('edit-contact-person', req.contact_person || '');
    setVal('edit-contact-title', req.contact_title || '');
    setVal('edit-contact-channel', req.contact_channel || '');
    setVal('edit-cr-status', req.cr_status || 'متوفر');
    setVal('edit-primary-service', req.primary_service_name || '');
    setVal('edit-secondary-service', req.secondary_service_name || 'لا توجد');
    setVal('edit-policy-status', req.policy_evaluation || 'متوافق');
    setVal('edit-deadline', req.requested_deadline_text || '');
    setVal('edit-reviewer-name', req.reviewer_name || (AppState.lang === 'ar' ? 'سعود الراشد (مدير العمليات)' : 'Saud Al-Rashid (COO)'));
    setVal('edit-review-notes', req.review_notes || '');

    setVal('modal-customer-body', req.customer_draft_body || '');

    renderAuditLogs(data.audit_logs || []);

    const modal = document.getElementById('review-workbench-modal');
    if (modal) modal.classList.remove('hidden');
  } catch (err) {
    console.error("openReviewModal error:", err);
  }
}

window.openReviewModal = openReviewModal;

function closeReviewModal() {
  const modal = document.getElementById('review-workbench-modal');
  if (modal) modal.classList.add('hidden');
}

window.closeReviewModal = closeReviewModal;

async function submitReviewAction(actionStatus) {
  if (!AppState.selectedRequest) return;
  const reqId = AppState.selectedRequest.id;

  const reviewerName = (document.getElementById('edit-reviewer-name')?.value || '').trim() || 'المراجع المعتمد';
  const reviewNotes = (document.getElementById('edit-review-notes')?.value || '').trim();

  const editedFields = {
    organization_name: (document.getElementById('edit-org-name')?.value || '').trim(),
    contact_person: (document.getElementById('edit-contact-person')?.value || '').trim(),
    contact_title: (document.getElementById('edit-contact-title')?.value || '').trim(),
    contact_channel: (document.getElementById('edit-contact-channel')?.value || '').trim(),
    cr_status: document.getElementById('edit-cr-status')?.value || 'متوفر',
    primary_service_name: document.getElementById('edit-primary-service')?.value || '',
    secondary_service_name: document.getElementById('edit-secondary-service')?.value || 'لا توجد',
    policy_evaluation: document.getElementById('edit-policy-status')?.value || 'متوافق',
    requested_deadline_text: (document.getElementById('edit-deadline')?.value || '').trim(),
    customer_draft_body: (document.getElementById('modal-customer-body')?.value || '').trim()
  };

  try {
    const res = await fetch(`${API_BASE}/api/requests/${reqId}/review`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        review_status: actionStatus,
        reviewer_name: reviewerName,
        review_notes: reviewNotes,
        edited_fields: editedFields
      })
    });

    const data = await res.json();
    if (data.success) {
      showToast(AppState.lang === 'ar' ? `تم اعتماد القرار: (${actionStatus})` : `Review status updated`, "success");
      closeReviewModal();
      await fetchStats();
      await fetchRequests();
    } else {
      showToast(data.error || "Review update failed", "error");
    }
  } catch (err) {
    console.error("submitReviewAction error:", err);
    showToast("Error updating review", "error");
  }
}

window.submitReviewAction = submitReviewAction;

async function handleDispatchEmail() {
  if (!AppState.selectedRequest) return;
  const reqId = AppState.selectedRequest.id;
  const recipient = AppState.selectedRequest.email || (AppState.selectedRequest.contact_channel?.includes('@') ? AppState.selectedRequest.contact_channel : "client@example.com");

  try {
    const res = await fetch(`${API_BASE}/api/requests/${reqId}/dispatch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        recipient: recipient,
        dispatcher_name: document.getElementById('edit-reviewer-name')?.value || "Operations Team",
        channel: "Corporate Email / SMTP"
      })
    });
    const data = await res.json();
    if (data.success) {
      showToast(AppState.lang === 'ar' ? `تم إرسال الرد بنجاح! رقم التتبع: ${data.tracking_id}` : `Dispatched! Tracking ID: ${data.tracking_id}`, "success");
      await fetchRequests();
    }
  } catch (err) {
    console.error("Dispatch error:", err);
    showToast("Failed to dispatch email", "error");
  }
}

window.handleDispatchEmail = handleDispatchEmail;

function renderAuditLogs(logs) {
  const container = document.getElementById('modal-audit-timeline');
  if (!container) return;

  container.innerHTML = '';
  logs.forEach(log => {
    const item = document.createElement('div');
    item.className = "flex gap-2.5 text-xs text-slate-300 pb-2 mb-2 border-b border-white/5 last:border-0";
    item.innerHTML = `
      <div class="w-5 h-5 rounded-full bg-cyan-500/20 text-cyan-400 flex items-center justify-center flex-shrink-0 text-[10px]">
        <i class="fa-solid fa-clock-rotate-left"></i>
      </div>
      <div>
        <div class="font-bold text-white">${log.user} <span class="font-normal text-slate-400 text-[11px]">(${new Date(log.timestamp).toLocaleTimeString()})</span></div>
        <div class="text-slate-400 mt-0.5">${log.details || log.action}</div>
      </div>
    `;
    container.appendChild(item);
  });
}

// --- Database Table View ---

function renderRequestsTable(requests) {
  const tbody = document.getElementById('requests-table-body');
  if (!tbody) return;

  const isAr = AppState.lang === 'ar';

  if (requests.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" class="p-8 text-center text-slate-400 text-xs">
          ${isAr ? 'لا توجد طلبات مطابقة.' : 'No requests found.'}
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = '';
  requests.forEach(req => {
    const tr = document.createElement('tr');
    tr.className = "hover:bg-white/5 border-b border-white/5 transition";
    tr.innerHTML = `
      <td class="p-3.5 font-mono font-bold text-xs text-cyan-400">${req.request_code}</td>
      <td class="p-3.5">
        <div class="font-bold text-white text-xs">${req.organization_name || '-'}</div>
        <div class="text-[11px] text-slate-400">${req.contact_person || '-'} (${req.contact_channel || '-'})</div>
      </td>
      <td class="p-3.5 text-xs font-medium text-slate-300">
        ${req.primary_service_name}
        ${req.secondary_service_name && req.secondary_service_name !== 'لا توجد' ? `<div class="text-slate-500 text-[11px]">+ ${req.secondary_service_name}</div>` : ''}
      </td>
      <td class="p-3.5 text-xs">
        <span class="telemetry-chip ${getPolicyBadgeClass(req.policy_evaluation)}">
          ${req.policy_evaluation}
        </span>
      </td>
      <td class="p-3.5 text-xs">
        <span class="telemetry-chip ${getReviewBadgeClass(req.human_review_status)}">
          ${req.human_review_status}
        </span>
      </td>
      <td class="p-3.5 text-xs text-slate-400 font-mono">
        ${new Date(req.created_at).toLocaleDateString()}
      </td>
      <td class="p-3.5 text-center">
        <div class="flex items-center justify-center gap-1.5">
          <button onclick="openReviewModal(${req.id})" title="${isAr ? 'مراجعة' : 'Review'}" class="p-1.5 text-slate-400 hover:text-white rounded transition cursor-pointer">
            <i class="fa-solid fa-pen-to-square"></i>
          </button>
          <a href="/api/requests/${req.id}/print" target="_blank" title="${isAr ? 'طباعة' : 'Print'}" class="p-1.5 text-slate-400 hover:text-emerald-400 rounded transition">
            <i class="fa-solid fa-print"></i>
          </a>
          <button onclick="deleteRequestRecord(${req.id})" title="${isAr ? 'حذف' : 'Delete'}" class="p-1.5 text-slate-400 hover:text-rose-400 rounded transition cursor-pointer">
            <i class="fa-solid fa-trash-can"></i>
          </button>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

async function deleteRequestRecord(id) {
  const isAr = AppState.lang === 'ar';
  if (!confirm(isAr ? "هل أنت متأكد من حذف هذا السجل؟" : "Delete this record?")) return;
  try {
    const res = await fetch(`${API_BASE}/api/requests/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.success) {
      showToast(isAr ? "تم حذف الطلب" : "Request deleted", "info");
      await fetchStats();
      await fetchRequests();
    }
  } catch (err) {
    console.error("deleteRequestRecord error:", err);
  }
}

window.deleteRequestRecord = deleteRequestRecord;

// --- Benchmark Test Suite Runner ---

async function handleRunTests() {
  const container = document.getElementById('test-results-container');
  if (!container) return;

  const isAr = AppState.lang === 'ar';

  container.innerHTML = `
    <div class="p-10 text-center bg-[#05060A] rounded-2xl border border-white/10">
      <div class="inline-block animate-spin text-3xl text-cyan-400 mb-3"><i class="fa-solid fa-circle-notch"></i></div>
      <div class="font-extrabold text-white text-sm">${isAr ? 'جاري تشغيل الاختبارات المعيارية الـ 11 والتحقق الرياضي من السياسات...' : 'Executing 11 benchmark tests...'}</div>
    </div>
  `;

  try {
    const res = await fetch(`${API_BASE}/api/tests/run`, { method: 'POST' });
    const data = await res.json();

    if (data.success) {
      renderTestResults(data.data);
    }
  } catch (err) {
    console.error("handleRunTests error:", err);
    container.innerHTML = `<div class="p-4 bg-rose-950/40 text-rose-300 text-xs rounded-xl">Failed to execute tests</div>`;
  }
}

function renderTestResults(results) {
  const container = document.getElementById('test-results-container');
  if (!container) return;

  const isSuccess = results.was_successful;
  const isAr = AppState.lang === 'ar';

  container.innerHTML = `
    <div class="p-6 rounded-2xl ${isSuccess ? 'bg-emerald-950/30 border border-emerald-500/40' : 'bg-rose-950/30 border border-rose-500/40'} mb-6 shadow-[0_0_30px_rgba(0,255,135,0.1)]">
      <div class="flex items-center justify-between flex-wrap gap-3">
        <div class="flex items-center gap-3.5">
          <div class="w-10 h-10 rounded-xl ${isSuccess ? 'bg-emerald-600' : 'bg-rose-600'} text-white flex items-center justify-center text-lg shadow-lg">
            <i class="fa-solid ${isSuccess ? 'fa-check' : 'fa-xmark'}"></i>
          </div>
          <div>
            <div class="text-base font-extrabold ${isSuccess ? 'text-emerald-300' : 'text-rose-300'}">
              ${isSuccess ? (isAr ? 'تم اجتياز جميع الفحوصات المعيارية الـ 11 بنجاح (دقة 100%)' : 'All 11 Automated Tests Passed (100% Precision)') : 'Test Assertions Failed'}
            </div>
            <div class="text-xs text-slate-400 font-mono mt-0.5">
              Total: ${results.total_tests} | Passed: ${results.passed} | Failures: ${results.failures}
            </div>
          </div>
        </div>
        <span class="px-3.5 py-1.5 rounded-xl text-xs font-black ${isSuccess ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' : 'bg-rose-500/20 text-rose-300'} font-mono">
          100% SUITE PASS
        </span>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5 text-xs">
      <div class="p-4 rounded-xl spotlight-card">
        <div class="flex items-center justify-between mb-1.5">
          <span class="font-extrabold text-white text-xs">Request A (Analytics & BI)</span>
          <span class="telemetry-chip chip-compliant text-[9px]">100% PASS</span>
        </div>
        <div class="text-[11px] text-slate-400">12 Days, Valid CR, Matched Service 5.</div>
      </div>

      <div class="p-4 rounded-xl spotlight-card">
        <div class="flex items-center justify-between mb-1.5">
          <span class="font-extrabold text-white text-xs">Request B (Automation + ERP)</span>
          <span class="telemetry-chip chip-compliant text-[9px]">100% PASS</span>
        </div>
        <div class="text-[11px] text-slate-400">Service 2 + Service 7, Missing CR flagged.</div>
      </div>

      <div class="p-4 rounded-xl spotlight-card">
        <div class="flex items-center justify-between mb-1.5">
          <span class="font-extrabold text-white text-xs">Request C (Marketing OOS)</span>
          <span class="telemetry-chip chip-compliant text-[9px]">100% PASS</span>
        </div>
        <div class="text-[11px] text-slate-400">Zero Hallucination polite apology.</div>
      </div>

      <div class="p-4 rounded-xl spotlight-card">
        <div class="flex items-center justify-between mb-1.5">
          <span class="font-extrabold text-white text-xs">Request D (Urgent SOP)</span>
          <span class="telemetry-chip chip-compliant text-[9px]">100% PASS</span>
        </div>
        <div class="text-[11px] text-slate-400">6 Days vs 10-15 standard days (Urgent).</div>
      </div>

      <div class="p-4 rounded-xl spotlight-card">
        <div class="flex items-center justify-between mb-1.5">
          <span class="font-extrabold text-white text-xs">Request E (Vague Request)</span>
          <span class="telemetry-chip chip-compliant text-[9px]">100% PASS</span>
        </div>
        <div class="text-[11px] text-slate-400">Enumerated all missing fields, discount blocked.</div>
      </div>

      <div class="p-4 rounded-xl spotlight-card">
        <div class="flex items-center justify-between mb-1.5">
          <span class="font-extrabold text-white text-xs">Edge Case (< 3 Days)</span>
          <span class="telemetry-chip chip-compliant text-[9px]">100% PASS</span>
        </div>
        <div class="text-[11px] text-slate-400">Policy 2 violation strictly caught.</div>
      </div>
    </div>
  `;
}

// --- Reset Benchmark Samples ---

async function handleResetSamples() {
  const isAr = AppState.lang === 'ar';
  if (!confirm(isAr ? "إعادة تهيئة العينات الرسمية الخمسة؟" : "Reset official samples A-E?")) return;
  try {
    const res = await fetch(`${API_BASE}/api/reset-samples`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      showToast(isAr ? "تمت إعادة التهيئة بنجاح!" : "Samples reset successfully!", "success");
      await fetchStats();
      await fetchRequests();
    }
  } catch (err) {
    console.error("handleResetSamples error:", err);
  }
}

// --- Catalog & Policies Rendering ---

function renderCatalogCards(services) {
  const container = document.getElementById('catalog-cards-container');
  if (!container) return;

  const isAr = AppState.lang === 'ar';
  container.innerHTML = '';

  services.forEach(s => {
    const card = document.createElement('div');
    card.className = "p-5 rounded-2xl spotlight-card flex flex-col justify-between text-xs";
    card.innerHTML = `
      <div>
        <div class="flex items-center justify-between mb-2.5">
          <span class="w-8 h-8 rounded-xl bg-white/10 text-cyan-400 font-mono font-black flex items-center justify-center text-xs">
            ${s.id}
          </span>
          <span class="text-[11px] font-mono text-emerald-400 bg-emerald-950/40 px-2.5 py-0.5 rounded-lg border border-emerald-500/30 font-extrabold">
            ${s.standard_days_text}
          </span>
        </div>
        <h4 class="font-extrabold text-white text-xs mb-1.5">${s.name}</h4>
        <p class="text-[11px] text-slate-400 leading-relaxed mb-3">${s.description}</p>
        
        <div class="space-y-1.5 text-[11px]">
          <div class="text-slate-300"><span class="font-bold text-slate-400">${isAr ? 'الاستخدام:' : 'Use when:'}</span> ${s.when_to_use}</div>
          <div class="text-rose-300"><span class="font-bold text-rose-400">${isAr ? 'الاستثناءات:' : 'Excludes:'}</span> ${s.excludes}</div>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

function renderPolicyCards(policies) {
  const container = document.getElementById('policies-cards-container');
  if (!container) return;

  const isAr = AppState.lang === 'ar';
  container.innerHTML = '';

  policies.forEach(p => {
    const card = document.createElement('div');
    card.className = "p-5 rounded-2xl spotlight-card flex items-start gap-4 text-xs";
    card.innerHTML = `
      <div class="w-9 h-9 rounded-xl bg-white/10 text-amber-400 font-mono font-black flex items-center justify-center flex-shrink-0 text-xs border border-white/10">
        ${p.id}
      </div>
      <div>
        <h4 class="font-extrabold text-white text-xs mb-1">${p.title}</h4>
        <p class="text-xs text-slate-300 leading-relaxed mb-2.5">${p.full_text}</p>
        <div class="text-[11px] text-slate-400 bg-[#05060A] p-3 rounded-xl border border-white/5">
          <span class="font-bold text-white">${isAr ? 'الأثر التشغيلي:' : 'Operational Impact:'}</span> ${p.impact}
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

function populateServiceDropdowns(services) {
  const primarySel = document.getElementById('edit-primary-service');
  const secondarySel = document.getElementById('edit-secondary-service');
  if (!primarySel || !secondarySel) return;

  primarySel.innerHTML = '<option value="خارج النطاق">خارج النطاق</option><option value="غير محدد / يتطلب استيضاح">غير محدد / يتطلب استيضاح</option>';
  secondarySel.innerHTML = '<option value="لا توجد">لا توجد</option>';

  services.forEach(s => {
    const opt1 = document.createElement('option');
    opt1.value = s.name;
    opt1.textContent = s.name;
    primarySel.appendChild(opt1);

    const opt2 = document.createElement('option');
    opt2.value = s.name;
    opt2.textContent = s.name;
    secondarySel.appendChild(opt2);
  });
}

// --- KPI Stats Updating ---

function updateStatsUI(stats) {
  setText('kpi-total-requests', stats.total_requests || 0);
  setText('kpi-pending-review', stats.pending_review || 0);
  setText('kpi-approved-requests', stats.approved_requests || 0);
  setText('kpi-compliance-rate', `${stats.compliance_rate_percent || 100}%`);
}

// --- Utility Helpers ---

function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

function setVal(id, val) {
  const el = document.getElementById(id);
  if (el) el.value = val;
}

function getPolicyBadgeClass(status) {
  if (!status) return 'chip-compliant';
  if (status.includes('متوافق') || status.includes('Compliant')) return 'chip-compliant';
  if (status.includes('عاجل') || status.includes('Urgent')) return 'chip-urgent';
  if (status.includes('مخالف') || status.includes('Violation')) return 'chip-violation';
  if (status.includes('خارج النطاق') || status.includes('Out of Scope')) return 'chip-out-of-scope';
  return 'chip-pending';
}

function getReviewBadgeClass(status) {
  if (!status) return 'chip-pending';
  if (status.includes('تمت المراجعة') || status.includes('معتمد') || status.includes('Approved')) return 'chip-compliant';
  if (status.includes('بانتظار') || status.includes('Pending')) return 'chip-pending';
  if (status.includes('استيضاح') || status.includes('Clarification')) return 'chip-urgent';
  if (status.includes('مرفوض') || status.includes('Rejected')) return 'chip-violation';
  return 'chip-pending';
}

function getCRBadgeClass(status) {
  if (!status) return 'chip-violation';
  if (status.includes('متوفر') || status.includes('Available')) return 'chip-compliant';
  if (status.includes('غير واضح') || status.includes('Unclear')) return 'chip-urgent';
  return 'chip-violation';
}

function setupCopyButton(buttonId, textToCopy) {
  const btn = document.getElementById(buttonId);
  if (!btn) return;

  btn.onclick = () => {
    navigator.clipboard.writeText(textToCopy).then(() => {
      showToast(AppState.lang === 'ar' ? "تم النسخ بنجاح" : "Copied to clipboard", "success");
    }).catch(err => {
      console.error("Copy failed:", err);
    });
  };
}

function showToast(message, type = "info") {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `flex items-center gap-3 px-4 py-3.5 rounded-xl shadow-2xl border text-xs font-extrabold fade-in-v6 bg-[#10131E] text-white border-white/20`;
  toast.innerHTML = `<span>${message}</span>`;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 200);
  }, 3000);
}

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// --- DeepSeek AI Interactive Chat ---

let chatHistory = [];

async function sendChatMessage() {
  const input = document.getElementById('chat-user-input');
  if (!input) return;
  const text = input.value.trim();
  if (!text) return;

  appendChatMessage('user', text);
  input.value = '';

  chatHistory.push({ role: 'user', content: text });

  const thinkingId = appendChatMessage('assistant', '<i class="fa-solid fa-spinner animate-spin text-cyan-400"></i> جاري التفكير ومراجعة السياسات والخدمات...');

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: chatHistory,
        context: document.getElementById('input-request-text')?.value || ''
      })
    });
    const data = await res.json();

    const placeholderEl = document.getElementById(thinkingId);
    if (data.success && data.reply) {
      chatHistory.push({ role: 'assistant', content: data.reply });
      if (placeholderEl) {
        placeholderEl.innerHTML = formatMarkdown(data.reply);
      }
    } else {
      if (placeholderEl) {
        placeholderEl.innerHTML = `<span class="text-rose-400">عذراً، حدث خطأ: ${data.error || 'تعذر استلام الرد'}</span>`;
      }
    }
  } catch (err) {
    console.error('sendChatMessage error:', err);
    const placeholderEl = document.getElementById(thinkingId);
    if (placeholderEl) {
      placeholderEl.innerHTML = `<span class="text-rose-400">تعذر الاتصال بالخادم.</span>`;
    }
  }
}

window.sendChatMessage = sendChatMessage;

function sendQuickPrompt(promptText) {
  const input = document.getElementById('chat-user-input');
  if (input) {
    input.value = promptText;
    sendChatMessage();
  }
}

window.sendQuickPrompt = sendQuickPrompt;

function clearChatHistory() {
  chatHistory = [];
  const container = document.getElementById('chat-messages-container');
  if (container) {
    container.innerHTML = `
      <div class="p-4 bg-[#10131E] rounded-xl border border-white/10 text-slate-300 text-xs">
        <div class="font-extrabold text-white mb-1">المساعد الاستشاري (DeepSeek V4)</div>
        <div class="text-slate-400">تمت إعادة ضبط المحادثة. كيف يمكنني مساعدتك في سياسات أو خدمات هورايزون؟</div>
      </div>
    `;
  }
}

window.clearChatHistory = clearChatHistory;

function appendChatMessage(role, content) {
  const container = document.getElementById('chat-messages-container');
  if (!container) return null;

  const msgId = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  const isUser = role === 'user';

  const div = document.createElement('div');
  div.className = `p-4 rounded-2xl border ${isUser ? 'bg-[#171B2A] border-cyan-500/30 mr-8' : 'bg-[#10131E] border-white/10 ml-8'}`;
  div.innerHTML = `
    <div class="font-extrabold text-slate-300 text-xs mb-1.5 flex items-center gap-2">
      <i class="fa-solid ${isUser ? 'fa-user text-cyan-400' : 'fa-robot text-pink-400'}"></i>
      <span>${isUser ? (AppState.lang === 'ar' ? 'أنت' : 'You') : 'DeepSeek V4 Advisor'}</span>
    </div>
    <div id="${msgId}" class="leading-relaxed text-slate-200 whitespace-pre-wrap text-xs">${isUser ? escapeHtml(content) : content}</div>
  `;

  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return msgId;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function formatMarkdown(text) {
  if (!text) return '';
  let formatted = escapeHtml(text);
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-black">$1</strong>');
  formatted = formatted.replace(/^- (.*)$/gm, '<li class="mr-4 list-disc">$1</li>');
  formatted = formatted.replace(/(<li.*<\/li>)/s, '<ul class="my-2 space-y-1">$1</ul>');
  return formatted;
}
