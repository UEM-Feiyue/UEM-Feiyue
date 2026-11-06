(() => {
  const params = new URLSearchParams(location.search);
  document.documentElement.dataset.view = params.has('category') || params.get('view') === 'all' ? 'archive' : 'home';
  try {
    const saved = localStorage.getItem('uem-theme');
    if (saved === 'light' || saved === 'dark') document.documentElement.dataset.theme = saved;
  } catch {}
})();
