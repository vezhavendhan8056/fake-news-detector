/* =============================================================================
   TruthLens — dashboard.js
   Dashboard charts, statistics and recent predictions.
   ============================================================================= */

// Helpers
const isDark = () => document.documentElement.getAttribute('data-theme') !== 'light';

function chartColors() {
  const dark = isDark();
  return {
    text:       dark ? '#9B8EC4' : '#4C3A7A',
    grid:       dark ? 'rgba(255,255,255,0.04)' : 'rgba(124,58,237,0.08)',
    fakeLine:   '#F87171',
    realLine:   '#34D399',
    fakeFill:   'rgba(248,113,113,0.08)',
    realFill:   'rgba(52,211,153,0.08)',
    tooltipBg:  dark ? '#0D081A' : '#EDE8FF',
    tooltipText:dark ? '#F0EDF8' : '#1A0A40',
  };
}

let lineChart = null;
let doughnutChart = null;
let barChart = null;

// Counter animation
function animateCounter(el, target, duration = 1000, suffix = '') {
  let start = 0;
  const step = (timestamp) => {
    if (!start) start = timestamp;
    const progress = Math.min((timestamp - start) / duration, 1);
    const value = progress * target;
    el.textContent = (target % 1 === 0 ? Math.floor(value) : value.toFixed(1)) + suffix;
    if (progress < 1) {
      window.requestAnimationFrame(step);
    } else {
      el.textContent = target + suffix;
    }
  };
  window.requestAnimationFrame(step);
}

// Format timestamp
function formatTimestamp(isoStr) {
  try {
    const date = new Date(isoStr);
    return date.toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (e) {
    return isoStr || '—';
  }
}

// ── Load Stats ────────────────────────────────────────────────────────────────
async function loadDashboardStats() {
  try {
    const res = await fetch('/api/stats');
    if (!res.ok) throw new Error('API failed');
    const stats = await res.json();
    renderStatCards(stats);
    renderCharts(stats);
    renderRecentPredictions(stats.recent || []);
  } catch (err) {
    console.error('Dashboard load error:', err);
    Toast.show('Failed to load dashboard statistics.', 'error');
  }
}

// ── Stat Cards ────────────────────────────────────────────────────────────────
function renderStatCards(stats) {
  const cards = {
    totalPredictions: document.getElementById('statTotal'),
    fakePredictions:  document.getElementById('statFake'),
    realPredictions:  document.getElementById('statReal'),
    modelAccuracy:    document.getElementById('statAccuracy'),
    avgConfidence:    document.getElementById('statConfidence'),
    trainSamples:     document.getElementById('statTrainSamples'),
  };

  if (cards.totalPredictions) animateCounter(cards.totalPredictions, stats.total_predictions || 0);
  if (cards.fakePredictions)  animateCounter(cards.fakePredictions,  stats.fake_count       || 0);
  if (cards.realPredictions)  animateCounter(cards.realPredictions,  stats.real_count       || 0);
  if (cards.modelAccuracy)    animateCounter(cards.modelAccuracy,    parseFloat(stats.model_accuracy) || 0, 1000, '%');
  if (cards.avgConfidence)    animateCounter(cards.avgConfidence,    Math.round(stats.avg_confidence || 0), 1000, '%');
  if (cards.trainSamples)     animateCounter(cards.trainSamples,     stats.training_samples || 0);

  // Percentage breakdown bars
  const total = stats.total_predictions || 0;
  if (total > 0) {
    const fakeRatio = Math.round((stats.fake_count / total) * 100);
    const realRatio = 100 - fakeRatio;

    const fakeBar = document.getElementById('fakeBar');
    const realBar = document.getElementById('realBar');
    const fakePct = document.getElementById('fakePct');
    const realPct = document.getElementById('realPct');

    if (fakeBar) fakeBar.style.width = fakeRatio + '%';
    if (realBar) realBar.style.width = realRatio + '%';
    if (fakePct) fakePct.textContent = fakeRatio + '%';
    if (realPct) realPct.textContent = realRatio + '%';
  }
}

// ── Render Charts ─────────────────────────────────────────────────────────────
function renderCharts(stats) {
  const colors = chartColors();

  // 1. Daily Trend (Line Chart)
  const lineCtx = document.getElementById('lineChart');
  if (lineCtx && stats.daily_trend) {
    const days = Object.keys(stats.daily_trend).sort();
    const fakeData = days.map(d => stats.daily_trend[d].fake);
    const realData = days.map(d => stats.daily_trend[d].real);
    const labels   = days.map(d => {
      const date = new Date(d);
      return date.toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric' });
    });

    if (lineChart) lineChart.destroy();

    lineChart = new Chart(lineCtx, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'Potentially Misleading',
            data: fakeData,
            borderColor: colors.fakeLine,
            backgroundColor: colors.fakeFill,
            fill: true,
            tension: 0.35,
            pointBackgroundColor: colors.fakeLine,
            pointBorderColor: 'transparent',
            pointRadius: 4,
            pointHoverRadius: 6,
          },
          {
            label: 'Likely True',
            data: realData,
            borderColor: colors.realLine,
            backgroundColor: colors.realFill,
            fill: true,
            tension: 0.35,
            pointBackgroundColor: colors.realLine,
            pointBorderColor: 'transparent',
            pointRadius: 4,
            pointHoverRadius: 6,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: {
            position: 'top',
            labels: { color: colors.text, font: { family: 'Inter', size: 11 }, padding: 15, boxWidth: 8, usePointStyle: true }
          },
          tooltip: {
            backgroundColor: colors.tooltipBg,
            titleColor: colors.tooltipText,
            bodyColor: colors.text,
            borderColor: colors.grid,
            borderWidth: 1,
            padding: 10,
          }
        },
        scales: {
          x: { grid: { color: colors.grid }, ticks: { color: colors.text } },
          y: { grid: { color: colors.grid }, ticks: { color: colors.text, precision: 0 }, beginAtZero: true }
        }
      }
    });
  }

  // 2. Distribution (Doughnut Chart)
  const doughnutCtx = document.getElementById('doughnutChart');
  if (doughnutCtx) {
    if (doughnutChart) doughnutChart.destroy();

    doughnutChart = new Chart(doughnutCtx, {
      type: 'doughnut',
      data: {
        labels: ['Misleading', 'Likely True'],
        datasets: [{
          data: [stats.fake_count || 0, stats.real_count || 0],
          backgroundColor: ['rgba(248,113,113,0.85)', 'rgba(52,211,153,0.85)'],
          borderColor: [colors.fakeLine, colors.realLine],
          borderWidth: 1,
          hoverOffset: 6,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '72%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: colors.text, font: { family: 'Inter', size: 11 }, padding: 15, boxWidth: 8, usePointStyle: true }
          },
          tooltip: {
            backgroundColor: colors.tooltipBg,
            titleColor: colors.tooltipText,
            bodyColor: colors.text,
            borderColor: colors.grid,
            borderWidth: 1,
          }
        }
      }
    });
  }

  // 3. Confidence Distribution (Bar Chart)
  const barCtx = document.getElementById('barChart');
  if (barCtx) {
    const bins = { '50–60%': 0, '60–70%': 0, '70–80%': 0, '80–90%': 0, '90–100%': 0 };
    (stats.recent || []).forEach(item => {
      const c = item.confidence || 0;
      if (c < 60) bins['50–60%']++;
      else if (c < 70) bins['60–70%']++;
      else if (c < 80) bins['70–80%']++;
      else if (c < 90) bins['80–90%']++;
      else bins['90–100%']++;
    });

    if (barChart) barChart.destroy();

    barChart = new Chart(barCtx, {
      type: 'bar',
      data: {
        labels: Object.keys(bins),
        datasets: [{
          data: Object.values(bins),
          backgroundColor: [
            'rgba(99,102,241,0.6)',
            'rgba(124,58,237,0.6)',
            'rgba(168,85,247,0.6)',
            'rgba(236,72,153,0.6)',
            'rgba(52,211,153,0.6)',
          ],
          borderColor: 'transparent',
          borderWidth: 0,
          borderRadius: 4,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: colors.tooltipBg,
            titleColor: colors.tooltipText,
            bodyColor: colors.text,
            borderColor: colors.grid,
            borderWidth: 1,
          }
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: colors.text } },
          y: { grid: { color: colors.grid }, ticks: { color: colors.text, precision: 0 }, beginAtZero: true }
        }
      }
    });
  }
}

// ── Recent Predictions Table ─────────────────────────────────────────────────
function renderRecentPredictions(recent) {
  const tbody = document.getElementById('recentTableBody');
  if (!tbody) return;

  if (!recent.length) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:48px;color:var(--text-muted);">No analysis history yet. <a href="/#detectorSection" style="color:var(--violet-mid);text-decoration:underline;">Analyse your first article →</a></td></tr>`;
    return;
  }

  tbody.innerHTML = recent.map(item => {
    const isFake = item.label === 'FAKE';
    const badge = isFake ? 'tl-badge red' : 'tl-badge green';
    const labelText = isFake ? 'Misleading' : 'True';
    return `
      <tr>
        <td><span class="${badge}">${labelText}</span></td>
        <td style="max-width:320px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--text-secondary);">${item.text_preview || '—'}</td>
        <td style="font-weight:700;color:${isFake ? '#F87171' : '#34D399'}">${item.confidence}%</td>
        <td style="color:var(--text-muted);">${item.prediction_ms?.toFixed(0) || '—'} ms</td>
        <td style="color:var(--text-muted);">${formatTimestamp(item.timestamp)}</td>
      </tr>
    `;
  }).join('');
}

// ── Refresh Dashboard ────────────────────────────────────────────────────────
function refreshDashboard() {
  const btn = document.getElementById('refreshBtn');
  if (btn) {
    btn.disabled = true;
    btn.textContent = '⏳ Refreshing…';
  }
  loadDashboardStats().finally(() => {
    if (btn) {
      btn.disabled = false;
      btn.textContent = '↺ Refresh';
    }
    Toast.show('Dashboard stats updated.', 'success');
  });
}

// ── Listen for Theme Change ──────────────────────────────────────────────────
const observer = new MutationObserver(() => {
  if (lineChart || doughnutChart || barChart) {
    loadDashboardStats();
  }
});
observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

// ── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadDashboardStats();
  const rb = document.getElementById('refreshBtn');
  if (rb) rb.addEventListener('click', refreshDashboard);

  // Auto-refresh every 60s
  setInterval(loadDashboardStats, 60000);
});
