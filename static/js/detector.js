/* =============================================================================
   TruthLens — detector.js
   Article detection UI — API calls remain unchanged.
   ============================================================================= */

const Detector = (() => {
  const API_PREDICT = '/api/predict';

  // DOM refs
  const textarea    = () => document.getElementById('newsTextarea');
  const analyseBtn  = () => document.getElementById('checkNewsBtn');
  const clearBtn    = () => document.getElementById('clearBtn');
  const resultArea  = () => document.getElementById('resultSection');
  const loadingEl   = () => document.getElementById('loadingSection');
  const charCountEl = () => document.getElementById('charCount');
  const wordCountEl = () => document.getElementById('wordCount');
  const readingEl   = () => document.getElementById('readingTime');
  const previewVerd = () => document.getElementById('previewVerdict');
  const previewConf = () => document.getElementById('previewConf');
  const previewBar  = () => document.getElementById('previewConfBar');
  const previewStatus = () => document.getElementById('previewStatus');
  const previewTime = () => document.getElementById('previewTime');
  const previewDefault = () => document.getElementById('previewDefault');

  // Helper to escape HTML safely
  const escapeHtml = (str) => {
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return (str || '').replace(/[&<>"']/g, m => map[m]);
  };

  // ── Sample Texts ────────────────────────────────────────────────────────────
  const SAMPLES = {
    real: `Scientists at NASA have confirmed the presence of water ice on the moon's surface using data from the Lunar Reconnaissance Orbiter. The findings, published in the journal Nature Astronomy, show that water ice is concentrated at the lunar poles in permanently shadowed regions. This discovery could have significant implications for future moon missions and the possibility of establishing a permanent human presence on the moon. The water ice could potentially be used for drinking water or converted into hydrogen fuel for spacecraft propulsion systems.`,
    fake: `SHOCKING REVELATION: Scientists at a secret government laboratory have discovered that a common kitchen ingredient can cure all known diseases including cancer, diabetes, HIV, and COVID-19. The miracle cure has been suppressed by Big Pharma for decades because it would eliminate their trillion-dollar drug industry. A whistleblower has come forward with documents proving that executives knew about this cure since the 1970s but chose to hide it from the public. SHARE THIS BEFORE IT GETS TAKEN DOWN! The government is trying to suppress this information because it threatens their control over the population!`,
    mixed: `According to multiple reports, the new government policy on renewable energy has received mixed responses from industry experts. While some economists argue the measures will boost green technology investment significantly over the next decade, others caution that implementation timelines remain overly optimistic. The policy, announced yesterday by the Ministry of Environment, proposes mandatory solar panel installations on all new commercial buildings by 2028. Critics have pointed to similar programs in neighbouring countries that failed due to inadequate infrastructure funding, while supporters cite the growing affordability of solar technology as a key enabling factor.`,
  };

  // ── Text Metrics ────────────────────────────────────────────────────────────
  const updateMetrics = (text) => {
    const chars  = text.length;
    const words  = text.trim() ? text.trim().split(/\s+/).length : 0;
    const reading = Math.max(1, Math.ceil(words / 200));
    if (charCountEl()) charCountEl().textContent = chars.toLocaleString();
    if (wordCountEl()) wordCountEl().textContent = words.toLocaleString();
    if (readingEl())   readingEl().textContent   = reading;
  };

  // ── Reset Preview ────────────────────────────────────────────────────────────
  const resetPreview = () => {
    const v = previewVerd();
    const c = previewConf();
    const b = previewBar();
    const s = previewStatus();
    const t = previewTime();
    if (v) { v.className = 'preview-status-badge idle'; v.textContent = 'Awaiting Input'; }
    if (c) { c.className = 'preview-conf-num idle'; c.textContent = '—'; }
    if (b) { b.style.width = '0%'; }
    if (s) s.textContent = 'Ready';
    if (t) t.textContent = '—';
  };

  // ── Update Preview ───────────────────────────────────────────────────────────
  const updatePreview = (data) => {
    const verdict = data.verdict || data.label;
    let cls = 'unverified';
    let label = 'Unverified';

    if (verdict === 'LIKELY TRUE' || verdict === 'REAL') {
      cls = 'real';
      label = '✓ Likely True';
    } else if (verdict === 'LIKELY FALSE' || verdict === 'FAKE') {
      cls = 'fake';
      label = '⚠ Likely False';
    }

    const conf = data.confidence.toFixed(1);

    const v = previewVerd();
    const c = previewConf();
    const b = previewBar();
    const s = previewStatus();
    const t = previewTime();

    if (v) { v.className = `preview-status-badge ${cls}`; v.textContent = label; }
    if (c) { c.className = `preview-conf-num ${cls}`; c.textContent = `${conf}%`; }
    if (b) { setTimeout(() => { b.style.width = `${conf}%`; }, 50); }
    if (s) s.textContent = 'Completed';
    if (t) t.textContent = `${data.prediction_ms?.toFixed(0) || '—'}ms`;
  };

  // ── Build Result HTML ─────────────────────────────────────────────────────────
  const buildResultHTML = (data) => {
    const verdict = data.verdict || data.label;
    let cls = 'unverified';
    let headerCls = 'unverified-h';
    let verdictLabel = 'Unverified / Needs Verification';

    if (verdict === 'LIKELY TRUE' || verdict === 'REAL') {
      cls = 'real';
      headerCls = 'real-h';
      verdictLabel = '✓ Likely True';
    } else if (verdict === 'LIKELY FALSE' || verdict === 'FAKE') {
      cls = 'fake';
      headerCls = 'fake-h';
      verdictLabel = '⚠ Likely False';
    }

    const conf      = parseFloat(data.confidence).toFixed(1);
    const fakeP     = parseFloat(data.fake_prob || 0).toFixed(1);
    const realP     = parseFloat(data.real_prob || 0).toFixed(1);

    const C = 239; // SVG circle circumference
    const dashOffset = C - (C * data.confidence / 100);

    // Supporting & Contradicting Evidence HTML lists
    let supportingHTML = '<p style="color:var(--text-muted);font-size:0.875rem;">No explicit supporting evidence found.</p>';
    if (data.supporting_evidence && data.supporting_evidence.length > 0) {
      supportingHTML = data.supporting_evidence.map(src => `
        <div class="evidence-card">
          <div class="evidence-card-meta">
            <span class="evidence-source-tag">${escapeHtml(src.domain)}</span>
            <span>${escapeHtml(src.pub_date)}</span>
          </div>
          <p style="color:var(--text-secondary);line-height:1.5;">${escapeHtml(src.snippet)}</p>
        </div>
      `).join('');
    }

    let contradictingHTML = '<p style="color:var(--text-muted);font-size:0.875rem;">No explicit contradicting evidence found.</p>';
    if (data.contradicting_evidence && data.contradicting_evidence.length > 0) {
      contradictingHTML = data.contradicting_evidence.map(src => `
        <div class="evidence-card">
          <div class="evidence-card-meta">
            <span class="evidence-source-tag">${escapeHtml(src.domain)}</span>
            <span style="color:#F87171;">${escapeHtml(src.pub_date)}</span>
          </div>
          <p style="color:var(--text-secondary);line-height:1.5;">${escapeHtml(src.snippet)}</p>
        </div>
      `).join('');
    }

    // Sources Checked HTML Grid
    let sourcesHTML = '';
    if (data.sources_checked && data.sources_checked.length > 0) {
      sourcesHTML = `
        <div class="label-xs" style="grid-column: 1 / -1; margin-bottom: 4px;">Authoritative Sources Verified</div>
        <div class="source-cards-grid" style="grid-column: 1 / -1; padding: 0; border: none; background: transparent;">
          ${data.sources_checked.map(src => {
            let badgeCls = 'cred-badge neutral';
            if (src.credibility >= 0.9) badgeCls = 'cred-badge high';
            else if (src.credibility <= 0.3 && src.credibility > 0) badgeCls = 'cred-badge low';
            else if (src.credibility === 0) badgeCls = 'cred-badge satire';

            return `
              <div class="source-item-card">
                <a href="${escapeHtml(src.url)}" target="_blank" rel="noopener" class="source-item-title" title="${escapeHtml(src.title)}">
                  ${escapeHtml(src.title)} ↗
                </a>
                <div class="source-item-footer">
                  <span class="${badgeCls}">${escapeHtml(src.credibility_label)}</span>
                  <span>${escapeHtml(src.domain)}</span>
                </div>
              </div>
            `;
          }).join('')}
        </div>
      `;
    } else {
      sourcesHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 20px; color: var(--text-muted); font-size: 0.875rem;">
          No external online references found. Verification is based entirely on language model patterns.
        </div>
      `;
    }

    return `
      <div class="result-card" role="region" aria-label="Analysis result: ${verdict}">
        <!-- Header -->
        <div class="result-card-header ${headerCls}">
          <div>
            <div class="label-xs" style="margin-bottom:8px; color:rgba(255,255,255,0.7);">TruthLens Verification Verdict</div>
            <div class="result-verdict ${cls}" aria-live="polite">
              ${verdictLabel}
            </div>
            <div style="font-size:0.8rem; color:var(--text-secondary); margin-top:4px;">
              Status: <strong>${escapeHtml(data.web_status_label || data.web_status)}</strong>
            </div>
          </div>
          <div class="conf-ring-wrap" role="img" aria-label="Confidence: ${conf}%">
            <svg viewBox="0 0 88 88">
              <circle class="ring-bg" cx="44" cy="44" r="38"/>
              <circle class="ring-fill ${cls}" cx="44" cy="44" r="38"
                stroke-dasharray="${C}"
                stroke-dashoffset="${C}"
                id="confRingFill"/>
            </svg>
            <div class="conf-ring-center">${conf}%</div>
          </div>
        </div>

        <!-- Stat Body -->
        <div class="result-card-body">
          <div class="result-stat-cell">
            <div class="rsc-label">Integrated Score</div>
            <div class="rsc-value ${cls === 'real' ? 'gradient-text' : ''}" style="${cls === 'fake' ? 'color:#F87171' : ''}">${conf}%</div>
          </div>
          <div class="result-stat-cell">
            <div class="rsc-label">ML Model Prediction</div>
            <div style="font-size:0.9rem; font-weight:700; color:var(--text-primary); margin-top:4px;">
              ${data.ml_label} (${data.ml_confidence}%)
            </div>
          </div>
          <div class="result-stat-cell">
            <div class="rsc-label">ML Fake Probability</div>
            <div class="prob-bar-wrap">
              <span style="font-family:var(--font-display);font-size:1.1rem;font-weight:800;color:#F87171;">${fakeP}%</span>
              <div class="prob-bar-track"><div class="prob-bar-fill fake" style="width:${fakeP}%"></div></div>
            </div>
          </div>
          <div class="result-stat-cell">
            <div class="rsc-label">ML Real Probability</div>
            <div class="prob-bar-wrap">
              <span style="font-family:var(--font-display);font-size:1.1rem;font-weight:800;color:#34D399;">${realP}%</span>
              <div class="prob-bar-track"><div class="prob-bar-fill real" style="width:${realP}%"></div></div>
            </div>
          </div>
          <div class="result-stat-cell">
            <div class="rsc-label">Word Count</div>
            <div class="rsc-value">${(data.word_count || 0).toLocaleString()}</div>
          </div>
          <div class="result-stat-cell">
            <div class="rsc-label">Claim Query Extracted</div>
            <div style="font-size:0.8125rem; font-weight:600; color:var(--text-secondary); margin-top:4px; max-width:240px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">
              "${escapeHtml(data.claim_query || 'N/A')}"
            </div>
          </div>
        </div>

        <!-- Evidence Columns -->
        <div class="evidence-layout">
          <div>
            <div class="evidence-col-title support">
              <span>✓ Supporting Evidence</span>
            </div>
            <div class="evidence-list">
              ${supportingHTML}
            </div>
          </div>
          <div>
            <div class="evidence-col-title contradict">
              <span>✕ Contradicting Evidence</span>
            </div>
            <div class="evidence-list">
              ${contradictingHTML}
            </div>
          </div>
        </div>

        <!-- Sources Checked -->
        <div class="source-cards-grid">
          ${sourcesHTML}
        </div>

        <!-- Explanation -->
        ${data.explanation ? `
        <div class="result-explanation">
          <div class="label-xs" style="margin-bottom:10px;">Why this verdict?</div>
          <p style="font-size:0.9rem;color:var(--text-secondary);line-height:1.8;">${data.explanation}</p>
        </div>` : ''}

        <!-- Actions -->
        <div class="result-actions-bar">
          <button class="btn btn-ghost" onclick="navigator.clipboard.writeText('TruthLens: ${verdict} (${conf}% confidence)').then(()=>Toast.show('Copied to clipboard','success'))" aria-label="Copy result">
            ⎘ Copy Verdict
          </button>
          <button class="btn btn-ghost" onclick="window.print()" aria-label="Print result">
            ⎙ Print Analysis
          </button>
          <span style="margin-left:auto;font-size:0.75rem;color:var(--text-muted); display:flex; flex-direction:column; align-items:flex-end; gap:2px;">
            <span>Last verified: ${data.last_verified || 'Recent'}</span>
            <span>ID: ${(data.id || '').slice(0,8)}…</span>
          </span>
        </div>

        <!-- Academic Disclaimer -->
        <div class="academic-disclaimer">
          <strong>Academic Disclaimer:</strong> This system provides an automated assessment based on machine-learning patterns and available evidence. It should not be treated as definitive proof of truth or falsehood.
        </div>
      </div>
    `;
  };

  // ── Animate Ring ──────────────────────────────────────────────────────────────
  const animateRing = (confidence) => {
    const fill = document.getElementById('confRingFill');
    if (!fill) return;
    const C = 239;
    setTimeout(() => {
      fill.style.transition = 'stroke-dashoffset 1.2s cubic-bezier(0.34,1.2,0.64,1)';
      fill.setAttribute('stroke-dashoffset', C - (C * confidence / 100));
    }, 80);
  };

  // ── Run Prediction ────────────────────────────────────────────────────────────
  const predict = async () => {
    const text = textarea()?.value?.trim();
    if (!text) { Toast.show('Please paste an article to analyse.', 'error'); return; }
    if (text.length < 20) { Toast.show('Please enter at least 20 characters for a reliable result.', 'error'); return; }

    // Show loading
    const loading = loadingEl();
    const result  = resultArea();
    const btn     = analyseBtn();
    const def     = previewDefault();

    if (loading) loading.classList.remove('hidden');
    if (result)  { result.classList.add('hidden'); result.innerHTML = ''; }
    if (btn)     { btn.disabled = true; btn.innerHTML = '<span class="tl-spinner" style="width:18px;height:18px;border-width:2px;"></span> Analysing…'; }
    if (previewStatus()) previewStatus().textContent = 'Running…';

    try {
      const resp = await fetch(API_PREDICT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });

      if (!resp.ok) throw new Error(`Server error: ${resp.status}`);
      const data = await resp.json();

      // Render result
      if (result) {
        result.innerHTML = buildResultHTML(data);
        result.classList.remove('hidden');
        result.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }

      updatePreview(data);
      animateRing(data.confidence);

      const label = data.label === 'REAL' ? 'Likely True' : 'Potentially Misleading';
      Toast.show(`${label} — ${data.confidence.toFixed(1)}% confidence`, data.label === 'REAL' ? 'success' : 'error');

    } catch (err) {
      console.error('Prediction error:', err);
      Toast.show('Analysis failed. Please check the server is running.', 'error');
      resetPreview();
      if (result) {
        result.innerHTML = `
          <div class="glass-card" style="text-align:center;padding:40px;">
            <div style="font-size:2rem;margin-bottom:12px;">⚠️</div>
            <p style="color:var(--text-secondary);">Unable to connect to the analysis server.</p>
            <p style="color:var(--text-muted);font-size:0.875rem;margin-top:6px;">${err.message}</p>
          </div>`;
        result.classList.remove('hidden');
      }
    } finally {
      if (loading) loading.classList.add('hidden');
      if (btn)     { btn.disabled = false; btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="7" cy="7" r="5" stroke="currentColor" stroke-width="1.8"/><path d="M11 11l3 3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg> Analyse Article'; }
    }
  };

  // ── Init ───────────────────────────────────────────────────────────────────────
  const init = () => {
    const ta = textarea();
    if (!ta) return;

    // Metrics on input
    ta.addEventListener('input', () => updateMetrics(ta.value));
    updateMetrics('');

    // Keyboard shortcut for analysis (Ctrl+Enter)
    ta.addEventListener('keydown', (e) => {
      if (e.ctrlKey && e.key === 'Enter') {
        e.preventDefault();
        predict();
      }
    });

    // Analyse button
    const ab = analyseBtn();
    if (ab) ab.addEventListener('click', predict);

    // Clear
    const cb = clearBtn();
    if (cb) cb.addEventListener('click', () => {
      ta.value = '';
      updateMetrics('');
      resetPreview();
      const res = resultArea();
      if (res) { res.innerHTML = ''; res.classList.add('hidden'); }
      ta.focus();
    });

    // Sample pills
    document.querySelectorAll('.sample-pill[data-sample]').forEach(pill => {
      pill.addEventListener('click', () => {
        const key = pill.dataset.sample;
        if (SAMPLES[key]) {
          ta.value = SAMPLES[key];
          updateMetrics(ta.value);
          ta.focus();
          Toast.show(`Sample loaded — click Analyse Article.`, 'info');
        }
      });
    });
  };

  return { init };
})();

document.addEventListener('DOMContentLoaded', Detector.init);
