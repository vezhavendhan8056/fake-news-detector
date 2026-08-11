/* =============================================================================
   TruthLens — history.js
   History page logic — keeps all API routes and logic, updates DOM selectors.
   ============================================================================= */

let allHistory  = [];
let searchQuery = '';

// Helper to escape HTML safely
function escapeHtml(str) {
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
  return (str || '').replace(/[&<>"']/g, m => map[m]);
}

// Helper to format timestamp
function formatTimestamp(isoStr) {
  try {
    const d = new Date(isoStr);
    return d.toLocaleString('en-IN', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (e) {
    return isoStr || '—';
  }
}

// ── Fetch History ────────────────────────────────────────────────────────────
async function loadHistory() {
  const listEl    = document.getElementById('historyList');
  const totalEl   = document.getElementById('historyTotal');
  const loadingEl = document.getElementById('historyLoading');

  if (loadingEl) loadingEl.classList.remove('hidden');
  if (listEl)    listEl.innerHTML = '';

  try {
    const res = await fetch('/api/history');
    if (!res.ok) throw new Error('API failed');
    const data = await res.json();
    allHistory = data.history || [];

    if (totalEl) totalEl.textContent = allHistory.length.toLocaleString();
    renderHistory(allHistory);

  } catch (err) {
    console.error('History load error:', err);
    Toast.show('Failed to load history.', 'error');
    if (listEl) {
      listEl.innerHTML = `
        <div class="empty-state-tl">
          <div class="empty-icon">⚠️</div>
          <h3>Could not load history</h3>
          <p>Please check your connection and try again.</p>
        </div>`;
    }
  } finally {
    if (loadingEl) loadingEl.classList.add('hidden');
  }
}

// ── Render List ───────────────────────────────────────────────────────────────
function renderHistory(items) {
  const listEl  = document.getElementById('historyList');
  const countEl = document.getElementById('filteredCount');
  if (!listEl) return;

  if (countEl) countEl.textContent = items.length.toLocaleString();

  if (!items.length) {
    listEl.innerHTML = `
      <div class="empty-state-tl">
        <div class="empty-icon">📭</div>
        <h3>No verifications found</h3>
        <p>${searchQuery ? 'Try a different search term.' : 'Analyse your first article on the <a href="/" style="color:var(--violet-mid);text-decoration:underline;">home page</a>.'}</p>
      </div>
    `;
    return;
  }

  listEl.innerHTML = items.map(item => {
    const isFake = item.label === 'FAKE';
    const date   = formatTimestamp(item.timestamp);
    const badgeCls = isFake ? 'history-label-badge fake' : 'history-label-badge real';
    const labelText = isFake ? 'Misleading' : 'True';

    return `
      <div class="history-item-tl" id="item-${item.id}">
        <span class="${badgeCls}">${labelText}</span>
        <div class="history-preview-text" title="${escapeHtml(item.text_preview)}">
          ${escapeHtml(item.text_preview || 'No preview available')}
        </div>
        <div class="history-meta-row">
          <span style="font-weight:700;color:${isFake ? '#F87171' : '#34D399'}">${item.confidence}%</span>
          <span style="opacity:0.6;">${item.word_count} words</span>
          <span style="opacity:0.5;font-size:0.75rem;">${date}</span>
          <button class="btn btn-danger btn-icon" onclick="deleteEntry('${item.id}')" title="Delete" style="width:32px;height:32px;border-radius:8px;">
            ✕
          </button>
        </div>
      </div>
    `;
  }).join('');
}

// ── Filter and Search ─────────────────────────────────────────────────────────
function filterHistory() {
  const q = (document.getElementById('searchInput')?.value || '').toLowerCase().trim();
  searchQuery = q;

  let filtered = allHistory;

  if (q) {
    filtered = allHistory.filter(item =>
      (item.text_preview || '').toLowerCase().includes(q) ||
      (item.label || '').toLowerCase().includes(q) ||
      (item.explanation || '').toLowerCase().includes(q)
    );
  }

  const activeFilterBtn = document.querySelector('.tl-filter-btn.active');
  const labelFilter = activeFilterBtn ? activeFilterBtn.dataset.filter : 'all';

  if (labelFilter !== 'all') {
    filtered = filtered.filter(item => item.label === labelFilter.toUpperCase());
  }

  renderHistory(filtered);
}

// ── Delete entry ──────────────────────────────────────────────────────────────
async function deleteEntry(id) {
  const itemEl = document.getElementById(`item-${id}`);

  try {
    const res = await fetch(`/api/history/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Delete failed');

    if (itemEl) {
      itemEl.style.transition = 'opacity 0.25s var(--ease), transform 0.25s var(--ease), height 0.25s var(--ease)';
      itemEl.style.opacity = '0';
      itemEl.style.transform = 'translateX(24px)';
      setTimeout(() => itemEl.remove(), 250);
    }

    allHistory = allHistory.filter(h => h.id !== id);
    const totalEl = document.getElementById('historyTotal');
    if (totalEl) totalEl.textContent = allHistory.length.toLocaleString();

    Toast.show('Analysis entry deleted.', 'success');

  } catch (err) {
    console.error('Delete error:', err);
    Toast.show('Failed to delete entry.', 'error');
  }
}

// ── Clear all ────────────────────────────────────────────────────────────────
async function clearAllHistory() {
  if (!confirm('Are you sure you want to permanently clear all history? This cannot be undone.')) return;

  try {
    const res = await fetch('/api/history', { method: 'DELETE' });
    if (!res.ok) throw new Error('Clear failed');

    allHistory = [];
    renderHistory([]);
    const totalEl = document.getElementById('historyTotal');
    if (totalEl) totalEl.textContent = '0';
    Toast.show('All verification history cleared.', 'success');

  } catch (err) {
    console.error('Clear history error:', err);
    Toast.show('Failed to clear history.', 'error');
  }
}

// ── Export CSV ───────────────────────────────────────────────────────────────
function exportCSV() {
  if (!allHistory.length) {
    Toast.show('No history to export.', 'error');
    return;
  }

  const headers = ['ID', 'Verdict', 'Confidence', 'Fake Prob', 'Real Prob', 'Word Count', 'Prediction Time (ms)', 'Timestamp', 'Text Preview'];
  const rows = allHistory.map(h => [
    h.id,
    h.label,
    h.confidence,
    h.fake_prob,
    h.real_prob,
    h.word_count,
    h.prediction_ms,
    h.timestamp,
    `"${(h.text_preview || '').replace(/"/g, '""')}"`
  ]);

  const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `truthlens-history-${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
  Toast.show('Verification history exported as CSV.', 'success');
}

// ── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadHistory();

  const searchInput = document.getElementById('searchInput');
  if (searchInput) searchInput.addEventListener('input', filterHistory);

  document.querySelectorAll('.tl-filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tl-filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      filterHistory();
    });
  });

  const clearAllBtn = document.getElementById('clearAllBtn');
  if (clearAllBtn) clearAllBtn.addEventListener('click', clearAllHistory);

  const exportBtn = document.getElementById('exportCsvBtn');
  if (exportBtn) exportBtn.addEventListener('click', exportCSV);

  const refreshBtn = document.getElementById('historyRefreshBtn');
  if (refreshBtn) refreshBtn.addEventListener('click', loadHistory);
});
