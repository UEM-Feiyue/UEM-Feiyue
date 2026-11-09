(() => {
  const params = new URLSearchParams(location.search);
  document.documentElement.dataset.view = params.has('category') || params.get('view') === 'all' ? 'archive' : 'home';
  try {
    if (localStorage.getItem('uem-sidebar') === 'collapsed') document.documentElement.dataset.sidebar = 'collapsed';
    const saved = localStorage.getItem('uem-theme');
    if (saved === 'light' || saved === 'dark') document.documentElement.dataset.theme = saved;
  } catch {}
})();
