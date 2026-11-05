(() => {
  // The saved theme is applied before CSS in theme-init.js, not during first paint.
  const root = document.documentElement;
  // Same three-way system / light / dark cycle as the personal site.
  const modes = ['system', 'light', 'dark'];
  const themeButton = document.querySelector('#theme-toggle');
  const systemTheme = matchMedia('(prefers-color-scheme: dark)');
  const syncThemeControls = () => {
    const mode = root.dataset.theme || 'system';
    const next = modes[(modes.indexOf(mode) + 1) % modes.length];
    const labels = {system:'跟随系统',light:'浅色模式',dark:'深色模式'};
    themeButton.dataset.mode = mode;
    themeButton.setAttribute('aria-label', '当前' + labels[mode] + '，切换到' + labels[next]);
    themeButton.title = labels[mode] + ' · 点击切换到' + labels[next];
    themeButton.querySelector('#theme-label').textContent = labels[mode];
  };
  themeButton?.addEventListener('click', () => {
    const mode = root.dataset.theme || 'system';
    const next = modes[(modes.indexOf(mode) + 1) % modes.length];
    if (next === 'system') delete root.dataset.theme;
    else root.dataset.theme = next;
    try { localStorage.setItem('uem-theme', next); } catch {}
    syncThemeControls();
  });
  systemTheme.addEventListener('change', syncThemeControls);
  window.addEventListener('storage', event => {
    if (event.key !== 'uem-theme') return;
    if (event.newValue === 'light' || event.newValue === 'dark') root.dataset.theme = event.newValue;
    else delete root.dataset.theme;
    syncThemeControls();
  });
  window.addEventListener('pageshow', syncThemeControls);
  syncThemeControls();
  // Native in-page directory: keyboard-accessible disclosure and active heading.
  const contents = document.querySelector('details.article-toc');
  if (contents) {
    const links = [...contents.querySelectorAll('a[href^="#"]')];
    const headings = links.map(link => document.getElementById(decodeURIComponent(link.hash.slice(1))));
    const update = () => {
      const probe = scrollY + 110;
      let active = 0;
      headings.forEach((heading, i) => {
        if (heading && heading.getBoundingClientRect().top + scrollY <= probe) active = i;
      });
      links.forEach((link, i) => {
        link.classList.toggle('is-active', i === active);
        if (i === active) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
      });
    };
    let pending = false;
    window.addEventListener('scroll', () => {
      if (pending) return;
      pending = true;
      requestAnimationFrame(() => { pending = false; update(); });
    }, {passive:true});
    update();
  }

  const sidebar = document.querySelector('#sidebar');
  const toggle = document.querySelector('#menu-toggle');
  const shell = document.querySelector('.shell');
  const mobile = matchMedia('(max-width: 900px)');
  const isOpen = () => mobile.matches && shell.classList.contains('menu-open');
  const setMenu = (open, restoreFocus = false) => {
    open = Boolean(open && mobile.matches);
    shell.classList.toggle('menu-open', open);
    sidebar.classList.toggle('open', open);
    sidebar.inert = mobile.matches && !open;
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? '关闭导航' : '打开导航');
    if (restoreFocus && mobile.matches) toggle.focus();
  };
  toggle.addEventListener('click', () => setMenu(!isOpen()));
  document.addEventListener('click', event => {
    if (isOpen() && !sidebar.contains(event.target) && !toggle.contains(event.target)) setMenu(false);
  });
  // Same-document category changes dismiss the panel before the content updates.
  // Cross-document links keep the outgoing panel stable until the new page loads,
  // avoiding a flash of the old page during navigation.
  sidebar.addEventListener('click', event => {
    const link = event.target.closest('a[href]');
    if (!link || !mobile.matches) return;
    const destination = new URL(link.href);
    const sameDocument = destination.origin === location.origin &&
      destination.pathname.replace(/index\\.html$/, '') === location.pathname.replace(/index\\.html$/, '');
    if (sameDocument) setMenu(false);
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && isOpen()) setMenu(false, true);
  });
  mobile.addEventListener('change', () => setMenu(false));
  window.addEventListener('pageshow', event => {
    if (event.persisted) setMenu(false);
  });
  setMenu(false);

  const archive = document.querySelector('#archive-section');
  if (!archive) return;
  const nav = document.querySelector('#category-nav');
  const year = document.querySelector('#year-filter');
  const search = document.querySelector('#search');
  // Native popover gives a fully styled menu and browser-managed light dismiss,
  // Escape, focus order and top-layer positioning. The select is the fallback.
  const yearTrigger = document.querySelector('#year-trigger');
  const yearMenu = document.querySelector('#year-options');
  if (yearMenu && typeof yearMenu.showPopover === 'function') {
    year.parentElement.classList.add('has-popover');
    yearTrigger.hidden = false;
    const options = [...year.options];
    const updateMenu = () => {
      document.querySelector('#year-label').textContent = year.selectedOptions[0]?.textContent || '全部届次';
      yearMenu.querySelectorAll('button').forEach(option => {
        const selected = option.dataset.value === year.value;
        option.setAttribute('aria-pressed', String(selected));
        option.classList.toggle('is-selected', selected);
      });
    };
    for (const option of options) {
      const item = document.createElement('button');
      item.type = 'button';
      item.className = 'year-option';
      item.dataset.value = option.value;
      item.textContent = option.textContent;
      item.addEventListener('click', () => {
        year.value = item.dataset.value;
        year.dispatchEvent(new Event('change', {bubbles:true}));
        yearMenu.hidePopover();
        yearTrigger.focus();
      });
      yearMenu.append(item);
    }
    const positionMenu = () => {
      const rect = yearTrigger.getBoundingClientRect();
      const width = Math.max(rect.width, 148);
      const spaceBelow = innerHeight - rect.bottom;
      yearMenu.style.width = width + 'px';
      yearMenu.style.left = Math.max(8, Math.min(rect.left, innerWidth - width - 8)) + 'px';
      yearMenu.style.top = (spaceBelow >= 130 ? rect.bottom + 6 :
        Math.max(8, rect.top - Math.min(yearMenu.scrollHeight || 150, 230) - 6)) + 'px';
    };
    yearMenu.addEventListener('beforetoggle', event => {
      if (event.newState === 'open') positionMenu();
    });
    window.addEventListener('resize', () => {
      if (yearMenu.matches(':popover-open')) positionMenu();
    }, {passive:true});
    window.addEventListener('scroll', () => {
      if (yearMenu.matches(':popover-open')) positionMenu();
    }, {passive:true});
    yearTrigger.addEventListener('click', () => {
      requestAnimationFrame(() => {
        if (yearMenu.matches(':popover-open')) yearMenu.querySelector('.is-selected')?.focus();
      });
    });
    yearTrigger.addEventListener('keydown', event => {
      if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
        event.preventDefault();
        yearMenu.showPopover();
        const options = [...yearMenu.querySelectorAll('button')];
        const current = options.findIndex(item => item.dataset.value === year.value);
        options[(current + (event.key === 'ArrowDown' ? 1 : options.length - 1)) % options.length].focus();
      }
    });
    yearMenu.addEventListener('keydown', event => {
      const items = [...yearMenu.querySelectorAll('button')];
      const index = items.indexOf(document.activeElement);
      let target = index;
      if (event.key === 'ArrowDown') target = (index + 1) % items.length;
      else if (event.key === 'ArrowUp') target = (index + items.length - 1) % items.length;
      else if (event.key === 'Home') target = 0;
      else if (event.key === 'End') target = items.length - 1;
      else return;
      event.preventDefault();
      items[target].focus();
    });
    year.addEventListener('change', updateMenu);
    year.addEventListener('yearsync', updateMenu);
    updateMenu();
  }

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
    year.dispatchEvent(new Event('yearsync'));
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
