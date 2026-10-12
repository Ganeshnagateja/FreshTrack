document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.getElementById('sidebar');
  const toggle = document.getElementById('menuToggle');
  if (sidebar && toggle) {
    toggle.addEventListener('click', () => sidebar.classList.toggle('is-open'));
    document.addEventListener('click', (event) => {
      if (window.innerWidth <= 980 && sidebar.classList.contains('is-open') && !sidebar.contains(event.target) && !toggle.contains(event.target)) {
        sidebar.classList.remove('is-open');
      }
    });
  }
  document.querySelectorAll('.message-close').forEach((button) => {
    button.addEventListener('click', () => button.closest('.message')?.remove());
  });
  document.querySelectorAll('[data-copy-target]').forEach((button) => {
    button.addEventListener('click', async () => {
      const element = document.getElementById(button.dataset.copyTarget);
      if (!element) return;
      const original = button.textContent;
      try {
        await navigator.clipboard.writeText(element.textContent.trim());
        button.textContent = 'Copied';
      } catch (_) {
        const range = document.createRange();
        range.selectNodeContents(element);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
        button.textContent = 'Select & copy';
      }
      window.setTimeout(() => { button.textContent = original; }, 1800);
    });
  });
});
