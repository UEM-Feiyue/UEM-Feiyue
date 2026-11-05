(() => {
  // The saved theme is applied before CSS in theme-init.js, not during first paint.
  const root = document.documentElement;
  const syncThemeControls = () => {
    const dark = root.dataset.theme === 'dark';
    document.querySelectorAll('#theme-toggle').forEach(button => {
      button.setAttribute('aria-label', dark ? '切换明亮主题' : '切换暗黑主题');
      button.setAttribute('aria-pressed', String(dark));
    });
  };
  document.querySelectorAll('#theme-toggle').forEach(button => button.addEventListener('click', () => {
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
  const siteRoot = new URL('./', location.href).pathname;
  const indexedPath = path => path.startsWith(siteRoot) ? '/' + path.slice(siteRoot.length) : path;
  const originalExcerpts = new Map(cards.map(card => [card, card.querySelector('.article-excerpt').textContent]));
  const status = document.querySelector('#search-status');
  const empty = document.querySelector('#empty-state');
  const count = document.querySelector('#results-count');
  let activeCategory = 'all';
  let matches = null;
  let searching = false;
  let requestId = 0;
  let engine;
  const loadSearch = () => engine ??= import('/pagefind/pagefind.js');
  const renderFilters = () => {
    let visibleCount = 0;
    let hasDemo = false;
    for (const card of cards) {
      const articleUrl = indexedPath(card.querySelector('h3 a').pathname);
      const visible = !searching && (matches === null || matches.has(articleUrl)) &&
        (activeCategory === 'all' || card.dataset.category === activeCategory) &&
        (year.value === 'all' || card.dataset.year === year.value);
      card.hidden = !visible;
      card.querySelector('.article-excerpt').textContent =
        matches?.get(articleUrl) || originalExcerpts.get(card);
      if (visible) {
        visibleCount++;
        hasDemo ||= card.dataset.demo === 'true';
      }
    }
    count.textContent = searching ? '正在搜索…' :
      visibleCount + ' 篇经历' + (hasDemo ? ' · 含演示内容' : '');
    empty.hidden = searching || visibleCount > 0;
  };
  const searchArticles = async () => {
    const query = search.value.trim();
    const id = ++requestId;
    matches = null;
    searching = Boolean(query);
    status.hidden = !query;
    if (!query) {
      status.textContent = '';
      renderFilters();
      return;
    }
    status.textContent = '正在搜索文章全文…';
    renderFilters();
    try {
      const pagefind = await loadSearch();
      const result = await pagefind.search(query);
      if (id !== requestId) return;
      const pages = await Promise.all(result.results.map(item => item.data()));
      if (id !== requestId) return;
      matches = new Map(pages.map(page => [new URL(page.url, location.href).pathname,
        page.plain_excerpt || page.meta?.title || '']));
      status.textContent = result.results.length ? '全文搜索结果' : '没有找到匹配内容';
    } catch (error) {
      if (id !== requestId) return;
      matches = new Map();
      status.textContent = '全文搜索暂不可用，请刷新页面后重试。';
      console.error('Pagefind search failed', error);
    } finally {
      if (id === requestId) {
        searching = false;
        renderFilters();
      }
    }
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
    searchArticles();
  };
  const filter = () => {
    history.replaceState({...history.state, search: search.value, year: year.value}, '');
    searchArticles();
  };
  search.addEventListener('input', filter);
  year.addEventListener('change', () => {
    history.replaceState({...history.state, search: search.value, year: year.value}, '');
    renderFilters();
  });
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
