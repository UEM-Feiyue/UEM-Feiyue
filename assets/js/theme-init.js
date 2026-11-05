(() => {
  try {
    const saved = localStorage.getItem('uem-theme');
    if (saved === 'light' || saved === 'dark') document.documentElement.dataset.theme = saved;
  } catch {}
})();
