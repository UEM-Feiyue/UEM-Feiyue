(() => {
  try {
    const theme = localStorage.getItem('uem-theme');
    if (theme === 'light' || theme === 'dark') document.documentElement.dataset.theme = theme;
  } catch {}
})();
