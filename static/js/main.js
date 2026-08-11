/* =============================================================================
   TruthLens — main.js
   Shared utilities: theme, navbar, toast, scroll animations
   ============================================================================= */

// ── Theme Manager ─────────────────────────────────────────────────────────────
const Theme = (() => {
  const KEY = 'tl-theme';
  const ICONS = { dark: '🌙', light: '☀️' };
  let current = localStorage.getItem(KEY) || 'dark';

  const apply = (theme) => {
    current = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(KEY, theme);
    document.querySelectorAll('#themeToggleBtn, #themeSwitch').forEach(btn => {
      if (btn) btn.textContent = ICONS[theme];
    });
  };

  const toggle = () => apply(current === 'dark' ? 'light' : 'dark');
  const init   = () => {
    apply(current);
    document.querySelectorAll('#themeToggleBtn, #themeSwitch').forEach(btn => {
      if (btn) btn.addEventListener('click', toggle);
    });
  };

  return { init, toggle, get: () => current };
})();

// ── Toast System ──────────────────────────────────────────────────────────────
const Toast = (() => {
  const ICONS = { success: '✓', error: '✕', info: 'ℹ' };

  const show = (message, type = 'info', duration = 3500) => {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `tl-toast ${type}`;
    toast.setAttribute('role', 'status');
    toast.innerHTML = `
      <span class="tl-toast-icon">${ICONS[type] || ICONS.info}</span>
      <span class="tl-toast-msg">${message}</span>
      <button class="tl-toast-close" aria-label="Dismiss notification">✕</button>
    `;

    const dismiss = () => {
      toast.classList.add('leaving');
      setTimeout(() => toast.remove(), 320);
    };

    toast.querySelector('.tl-toast-close').addEventListener('click', dismiss);
    container.appendChild(toast);
    setTimeout(dismiss, duration);
  };

  return { show };
})();

// ── Mobile Navigation ──────────────────────────────────────────────────────────
const MobileNav = (() => {
  const init = () => {
    const btn     = document.getElementById('mobileMenuBtn');
    const mobileNav = document.getElementById('mobileNav');
    if (!btn || !mobileNav) return;

    const toggle = () => {
      const isOpen = mobileNav.classList.toggle('open');
      btn.classList.toggle('open', isOpen);
      btn.setAttribute('aria-expanded', isOpen);
    };

    btn.addEventListener('click', toggle);

    // Close on link click
    mobileNav.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', () => {
        mobileNav.classList.remove('open');
        btn.classList.remove('open');
        btn.setAttribute('aria-expanded', 'false');
      });
    });

    // Close on outside click
    document.addEventListener('click', (e) => {
      if (!btn.contains(e.target) && !mobileNav.contains(e.target)) {
        mobileNav.classList.remove('open');
        btn.classList.remove('open');
        btn.setAttribute('aria-expanded', 'false');
      }
    });
  };
  return { init };
})();

// ── Scroll Animations ──────────────────────────────────────────────────────────
const ScrollAnim = (() => {
  const init = () => {
    const obs = new IntersectionObserver((entries) => {
      entries.forEach((entry, i) => {
        if (entry.isIntersecting) {
          setTimeout(() => entry.target.classList.add('visible'), i * 60);
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

    document.querySelectorAll('.anim-in').forEach(el => obs.observe(el));
  };
  return { init };
})();

// ── Smooth Anchor Scroll ───────────────────────────────────────────────────────
const SmoothScroll = (() => {
  const init = () => {
    document.querySelectorAll('a[href^="#"]').forEach(a => {
      a.addEventListener('click', (e) => {
        const id = a.getAttribute('href').slice(1);
        const target = document.getElementById(id);
        if (target) {
          e.preventDefault();
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      });
    });
  };
  return { init };
})();

// ── Keyboard Shortcut: Ctrl+Enter ─────────────────────────────────────────────
const KeyShortcuts = (() => {
  const init = () => {
    document.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        const analyseBtn = document.getElementById('checkNewsBtn');
        if (analyseBtn && document.getElementById('newsTextarea')?.value.trim()) {
          analyseBtn.click();
        }
      }
    });
  };
  return { init };
})();

// ── Init ───────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  Theme.init();
  MobileNav.init();
  ScrollAnim.init();
  SmoothScroll.init();
  KeyShortcuts.init();
});
