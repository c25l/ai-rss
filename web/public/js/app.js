/* H3lPeR Web — Minimal client-side JS */

// Dark mode toggle (using Pico's data-theme)
document.addEventListener('DOMContentLoaded', () => {
  // Restore theme preference
  const saved = localStorage.getItem('h3lper-theme');
  if (saved) {
    document.documentElement.setAttribute('data-theme', saved);
  }
});

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('h3lper-theme', next);
}
