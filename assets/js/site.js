(() => {
  // The saved theme is applied before CSS in theme-init.js, not during first paint.
  const root = document.documentElement;
  const syncThemeControls = () => {
    const dark = root.dataset.theme === 'dark';
    document.querySelectorAll('#theme-toggle, #theme-toggle-mobile').forEach(button => {
      button.setAttribute('aria-label', dark ? '切换明亮主题' : '切换暗黑主题');
      button.setAttribute('aria-pressed', String(dark));
    });
  };
  document.querySelectorAll('#theme-toggle, #theme-toggle-mobile').forEach(button => button.addEventListener('click', () => {
    const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    try { localStorage.setItem('uem-theme', next); } catch {}
    syncThemeControls();
  }));
  window.addEventListener('storage', event => {
    if (event.key !== 'uem-theme') return;
    if (event.newValue === 'dark' || event.newValue === 'light') root.dataset.theme = event.newValue;
    else delete root.dataset.theme;
    syncThemeControls();
  });
  window.addEventListener('pageshow', syncThemeControls);
  syncThemeControls();

  const sidebar = document.querySelector('#sidebar');
  const toggle = document.querySelector('#menu-toggle');
  const mobile = matchMedia('(max-width: 900px)');
  const syncMenu = () => { sidebar.inert = mobile.matches && !sidebar.classList.contains('open'); };
  const closeMenu = (restoreFocus = false) => {
    sidebar.classList.remove('open');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-label', '打开导航');
    syncMenu();
    if (restoreFocus && mobile.matches) toggle.focus();
  };
  toggle?.addEventListener('click', () => {
    const open = sidebar.classList.toggle('open');
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? '关闭导航' : '打开导航');
    syncMenu();
  });
  document.addEventListener('click', event => {
    if (sidebar.classList.contains('open') && !sidebar.contains(event.target) && !toggle.contains(event.target)) closeMenu();
  });
  sidebar?.addEventListener('click', event => {
    if (event.target.closest('a')) closeMenu();
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && sidebar.classList.contains('open')) closeMenu(true);
  });
  mobile.addEventListener('change', () => closeMenu());
  syncMenu();

  const archive = document.querySelector('#archive-section');
  if (!archive) return;
  const nav = document.querySelector('#category-nav');
  const year = document.querySelector('#year-filter');
  const search = document.querySelector('#search');
  const cards = [...archive.querySelectorAll('.article-item')];
  let activeCategory = 'all';
  const renderFilters = () => {
    const query = search.value.trim().toLocaleLowerCase();
    let count = 0, hasDemo = false;
    for (const card of cards) {
      const visible = (activeCategory === 'all' || card.dataset.category === activeCategory) &&
        (year.value === 'all' || card.dataset.year === year.value) &&
        card.dataset.search.toLocaleLowerCase().includes(query);
      card.hidden = !visible;
      if (visible) { count++; hasDemo ||= card.dataset.demo === 'true'; }
    }
    document.querySelector('#results-count').textContent = count + ' 篇经历' + (hasDemo ? ' · 含演示内容' : '');
    document.querySelector('#empty-state').hidden = count > 0;
  };
  const renderView = () => {
    const params = new URLSearchParams(location.search);
    const selected = params.get('category');
    const isHome = !selected && params.get('view') !== 'all';
    document.querySelector('.page').classList.toggle('is-home', isHome);
    document.querySelector('#home-intro').hidden = !isHome;
    document.querySelector('#archive-intro').hidden = isHome;
    archive.hidden = isHome;
    const current = [...nav.querySelectorAll('[data-category]')].find(link => link.dataset.category === selected && selected !== 'all');
    activeCategory = current?.dataset.category || 'all';
    nav.querySelectorAll('[aria-current]').forEach(link => link.removeAttribute('aria-current'));
    const active = isHome ? nav.querySelector('a:not([data-category])') : current || nav.querySelector('[data-category="all"]');
    active?.setAttribute('aria-current', 'page');
    document.querySelector('#stories-heading').textContent = current ? current.dataset.categoryLabel + '经历' : '全部经历';
    document.querySelector('#category-intro').textContent = current ? current.dataset.categoryDescription + '，阅读同学的经验分享。' : '按方向浏览同学分享的升学与职业经验。';
    search.value = history.state?.search || '';
    year.value = history.state?.year || 'all';
    renderFilters();
  };
  const filter = () => {
    history.replaceState({...history.state, search: search.value, year: year.value}, '');
    renderFilters();
  };
  search.addEventListener('input', filter);
  year.addEventListener('change', filter);
  const indexPath = path => path.replace(/index\.html$/, '');
  document.addEventListener('click', event => {
    const link = event.target.closest('a[href]');
    if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || link.hasAttribute('download') || (link.target && link.target !== '_self')) return;
    const url = new URL(link.href);
    if (url.origin !== location.origin || indexPath(url.pathname) !== indexPath(location.pathname) || url.hash) return;
    event.preventDefault();
    if (url.href === location.href) return;
    history.pushState({search: '', year: 'all'}, '', url);
    const update = () => {
      renderView();
      window.scrollTo(0, 0);
      const heading = document.querySelector(archive.hidden ? '#hero-title' : '#stories-heading');
      heading?.setAttribute('tabindex', '-1');
      heading?.focus({preventScroll: true});
    };
    if (document.startViewTransition && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
      const transition = document.startViewTransition(update);
      transition.ready.catch(error => {
        if (error.name !== 'AbortError' && error.name !== 'InvalidStateError') throw error;
      });
    } else update();
  });
  window.addEventListener('popstate', renderView);
  renderView();
})();
