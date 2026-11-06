(() => {
  // The saved theme is applied before CSS in theme-init.js, not during first paint.
  const root = document.documentElement;
  const siteName = document.querySelector('.footer-brand-name')?.textContent.trim();
  const sourceUrl = document.querySelector('.footer-github')?.href;
  if (siteName && sourceUrl) {
    const styles = getComputedStyle(root);
    const accent = styles.getPropertyValue('--accent').trim();
    console.info(`%c ${siteName} %c ${sourceUrl}`,
      `background:${accent};color:${styles.getPropertyValue('--bg').trim()};font-weight:700;padding:5px 8px;border-radius:6px 0 0 6px`,
      `background:${styles.getPropertyValue('--soft').trim()};color:${accent};padding:5px 8px;border-radius:0 6px 6px 0`);
  }
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
  // Match the personal site's article directory while retaining native details.
  const initArticleToc = article => {
    const contents = article.querySelector('details.article-toc');
    if (!contents) return;
    const panel = contents.querySelector('.article-toc-panel');
    const summary = contents.querySelector('summary');
    const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
    contents.classList.add('is-enhanced');
    let closing = false;
    let navigating = false;
    let pendingTarget = null;
    summary.addEventListener('click', event => {
      event.preventDefault();
      navigating = false;
      if (reducedMotion.matches) {
        contents.open = !contents.open;
        contents.classList.toggle('is-open', contents.open);
        return;
      }
      if (closing) closing = false;
      if (contents.open && contents.classList.contains('is-open')) {
        contents.classList.remove('is-open');
        closing = true;
      } else {
        contents.open = true;
        requestAnimationFrame(() => contents.classList.add('is-open'));
      }
    });
    panel.addEventListener('transitionend', event => {
      if (event.target !== panel || event.propertyName !== 'grid-template-rows') return;
      if (closing) {
        contents.open = false;
        closing = false;
      } else if (pendingTarget) {
        const target = pendingTarget;
        pendingTarget = null;
        scrollToTarget(target);
      } else if (contents.open && !reducedMotion.matches && !navigating) {
        const overflow = contents.getBoundingClientRect().bottom - (innerHeight - 24);
        if (overflow > 0) scrollBy({top: overflow, behavior: 'smooth'});
      }
    });
    const links = [...contents.querySelectorAll('a[href^="#"]')];
    const headings = links.map(link => document.getElementById(decodeURIComponent(link.hash.slice(1))));
    let clickedTarget = null;
    const scrollToTarget = target => {
      const offset = parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop) || 0;
      const top = Math.max(0, Math.min(target.getBoundingClientRect().top + scrollY - offset, document.documentElement.scrollHeight - innerHeight));
      clickedTarget = {target, top, settled: false};
      scrollTo({top, behavior: reducedMotion.matches ? 'instant' : 'smooth'});
      update();
    };
    links.forEach(link => link.addEventListener('click', event => {
      const target = document.getElementById(decodeURIComponent(link.hash.slice(1)));
      if (!target) return;
      event.preventDefault();
      navigating = true;
      history.pushState(null, '', link.hash);
      if (panel.getAnimations().some(animation => animation.playState === 'running')) {
        pendingTarget = target;
      } else {
        scrollToTarget(target);
      }
    }));
    const update = () => {
      const probe = scrollY + (parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop) || 0) + 28;
      let active = 0;
      headings.forEach((heading, i) => {
        if (heading && heading.getBoundingClientRect().top + scrollY <= probe) active = i;
      });
      if (innerHeight + scrollY >= document.documentElement.scrollHeight - 6) active = headings.length - 1;
      if (clickedTarget) {
        if (Math.abs(scrollY - clickedTarget.top) <= 2) clickedTarget.settled = true;
        else if (clickedTarget.settled) clickedTarget = null;
        if (clickedTarget) active = headings.indexOf(clickedTarget.target);
      }
      links.forEach((link, i) => {
        link.classList.toggle('is-active', i === active);
        if (i === active) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
      });
    };
    const releaseTarget = () => { clickedTarget = null; update(); };
    window.addEventListener('wheel', releaseTarget, {passive:true});
    window.addEventListener('touchstart', releaseTarget, {passive:true});
    document.addEventListener('keydown', event => {
      if (['ArrowUp', 'ArrowDown', 'PageUp', 'PageDown', 'Home', 'End', ' '].includes(event.key)) releaseTarget();
    });
    let pending = false;
    window.addEventListener('scroll', () => {
      if (pending) return;
      pending = true;
      requestAnimationFrame(() => { pending = false; update(); });
    }, {passive:true});
    window.addEventListener('resize', releaseTarget, {passive:true});
    window.addEventListener('hashchange', () => {
      const target = headings.find(heading => heading?.id === decodeURIComponent(location.hash.slice(1)));
      clickedTarget = target ? {target, top: scrollY, settled: true} : null;
      update();
    });
    update();
  };
  window.initArticleToc = initArticleToc;
  document.querySelectorAll('.article-page:not(#preview-text)').forEach(initArticleToc);

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
  // Navigation has its own lifecycle: dismiss the outgoing menu synchronously,
  // without replaying its closing animation over the old or restored page.
  const resetMenu = () => {
    shell.classList.add('nav-reset');
    setMenu(false);
  };
  const finishReset = () => requestAnimationFrame(() => shell.classList.remove('nav-reset'));
  toggle.addEventListener('click', () => {
    shell.classList.remove('nav-reset');
    setMenu(!isOpen());
  });
  document.addEventListener('click', event => {
    if (isOpen() && !sidebar.contains(event.target) && !toggle.contains(event.target)) setMenu(false);
  });
  sidebar.addEventListener('click', event => {
    const link = event.target.closest('a[href]');
    if (!isOpen() || !link || event.defaultPrevented || event.button !== 0 ||
        event.metaKey || event.ctrlKey || event.shiftKey || event.altKey ||
        link.hasAttribute('download') || (link.target && link.target !== '_self')) return;
    const destination = new URL(link.href);
    if (destination.origin !== location.origin) return;
    resetMenu();
    const sameDocument = destination.pathname.replace(/index\.html$/, '') ===
      location.pathname.replace(/index\.html$/, '');
    // In-page links finish immediately; regular navigation retains the reset
    // state until pagehide, so no outgoing menu panel can flash.
    if (sameDocument) finishReset();
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && isOpen()) setMenu(false, true);
  });
  mobile.addEventListener('change', () => setMenu(false));
  window.addEventListener('pagehide', resetMenu);
  window.addEventListener('pageshow', () => {
    resetMenu();
    finishReset();
  });
  setMenu(false);

  const archive = document.querySelector('#archive-section');
  if (!archive) return;
  const nav = document.querySelector('#category-nav');
  const year = document.querySelector('#year-filter');
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
      const width = Math.max(rect.width, 108);
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
  const cardByPath = new Map(cards.map(card => [indexedPath(card.querySelector('h3 a').pathname), card]));
  const highlight = (element, value, query) => {
    const terms = [...new Set(query.split(/\s+/))].sort((a, b) => b.length - a.length);
    const pattern = new RegExp(terms.map(term => term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|'), 'giu');
    let end = 0;
    for (const match of value.matchAll(pattern)) {
      element.append(value.slice(end, match.index));
      const mark = document.createElement('mark');
      mark.textContent = match[0];
      element.append(mark);
      end = match.index + match[0].length;
    }
    element.append(value.slice(end));
  };
  const empty = document.querySelector('#empty-state');
  const count = document.querySelector('#results-count');
  let activeCategory = 'all';
  const renderFilters = () => {
    let visibleCount = 0;
    let hasDemo = false;
    for (const card of cards) {
      const visible = (activeCategory === 'all' || card.dataset.category === activeCategory) &&
        (year.value === 'all' || card.dataset.year === year.value);
      card.hidden = !visible;
      if (visible) {
        visibleCount++;
        hasDemo ||= card.dataset.demo === 'true';
      }
    }
    count.textContent = visibleCount + ' 篇经历' + (hasDemo ? ' · 含演示内容' : '');
    empty.hidden = visibleCount > 0;
  };
  const dialog = document.querySelector('#search-dialog');
  const search = document.querySelector('#search');
  const searchOpen = document.querySelector('.search-open');
  const results = document.querySelector('#search-results');
  const scrollHint = document.createElement('div');
  scrollHint.className = 'scroll-hint';
  scrollHint.setAttribute('aria-hidden', 'true');
  dialog.append(scrollHint);
  const syncScrollHint = () => {
    scrollHint.classList.toggle('is-visible', results.scrollHeight - results.clientHeight - results.scrollTop > 2);
  };
  results.addEventListener('scroll', syncScrollHint, {passive:true});
  new ResizeObserver(syncScrollHint).observe(results);
  let engine;
  let requestId = 0;
  const loadSearch = () => engine ??= import('/pagefind/pagefind.js').then(async pagefind => {
    await pagefind.options({ excerptLength: 18, excerptEllipsis: '…' });
    return pagefind;
  });
  const positionSearch = () => {
    if (mobile.matches) {
      const viewport = window.visualViewport;
      const height = viewport?.height || innerHeight;
      const offset = viewport?.offsetTop || 0;
      const available = Math.max(120, height - 24);
      dialog.style.setProperty('--search-top', Math.round(offset + Math.max(12, (height - Math.min(dialog.offsetHeight || 80, available)) / 2)) + 'px');
      dialog.style.setProperty('--search-available', Math.round(available) + 'px');
      return;
    }
    dialog.style.setProperty('--search-top', Math.round(searchOpen.getBoundingClientRect().bottom + 12) + 'px');
    dialog.style.removeProperty('--search-available');
  };
  const openSearch = () => {
    if (archive.hidden) return;
    if (mobile.matches) searchOpen.scrollIntoView({block:'center', behavior:'instant'});
    positionSearch();
    dialog.showModal();
    search.focus({preventScroll:true});
    requestAnimationFrame(positionSearch);
    syncScrollHint();
  };
  searchOpen.hidden = false;
  searchOpen.addEventListener('click', openSearch);
  window.addEventListener('resize', () => { if (dialog.open) positionSearch(); });
  window.visualViewport?.addEventListener('resize', () => { if (dialog.open) positionSearch(); });
  dialog.addEventListener('close', () => {
    ++requestId;
    search.value = '';
    results.replaceChildren();
    syncScrollHint();
    if (!archive.hidden) searchOpen.focus({preventScroll:true});
  });
  dialog.querySelector('.search-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
  document.addEventListener('keydown', event => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      if (dialog.open) dialog.close(); else openSearch();
    } else if (event.key === 'Escape' && dialog.open) {
      event.preventDefault();
      dialog.close();
    }
  });
  search.addEventListener('input', async () => {
    const query = search.value.trim();
    const id = ++requestId;
    results.replaceChildren();
    results.scrollTop = 0;
    syncScrollHint();
    if (!query) return;
    results.textContent = '正在搜索…';
    try {
      const pagefind = await loadSearch();
      const found = await pagefind.debouncedSearch(query);
      if (id !== requestId) return;
      const pages = await Promise.all((found?.results || []).map(item => item.data()));
      if (id !== requestId) return;
      const titleQuery = query.normalize('NFKC').toLocaleLowerCase();
      const exactCjkPhrase = /^[\p{Script=Han}]{2,}$/u.test(query);
      const indexed = new Set(pages.map(page => new URL(page.url, location.href).pathname));
      for (const [path, card] of cardByPath) {
        if (card.hidden || indexed.has(path)) continue;
        const title = card.querySelector('h3 a').textContent;
        const byline = card.querySelector('.article-meta').textContent;
        if (!(title + ' ' + byline).normalize('NFKC').toLocaleLowerCase().includes(titleQuery)) continue;
        pages.push({url: path, meta: {title, byline}, content: '', excerpt: ''});
      }
      pages.sort((a, b) => Number((b.meta.title + ' ' + (b.meta.byline || '')).normalize('NFKC').toLocaleLowerCase().includes(titleQuery)) -
        Number((a.meta.title + ' ' + (a.meta.byline || '')).normalize('NFKC').toLocaleLowerCase().includes(titleQuery)));
      const list = document.createElement('ul');
      for (const page of pages) {
        const card = cardByPath.get(new URL(page.url, location.href).pathname);
        if (!card || card.hidden) continue;
        if (exactCjkPhrase && !card.querySelector('h3 a').textContent.includes(query) && !(page.meta.byline || '').includes(query) && !page.content.includes(query)) continue;
        const row = document.createElement('li');
        const link = document.createElement('a');
        link.href = card.querySelector('h3 a').href;
        const title = document.createElement('span');
        title.className = 'search-title';
        highlight(title, card.querySelector('h3 a').textContent, query);
        link.append(title);
        const byline = card.querySelector('.article-meta').textContent;
        const position = exactCjkPhrase ? page.content.indexOf(query) : -1;
        if (byline.normalize('NFKC').toLocaleLowerCase().includes(titleQuery) || position >= 0 || page.excerpt?.includes('<mark>')) {
          const note = document.createElement('span');
          note.className = 'search-match';
          if (byline.normalize('NFKC').toLocaleLowerCase().includes(titleQuery)) {
            highlight(note, byline, query);
          } else if (position >= 0) {
            highlight(note, page.content.slice(Math.max(0, position - 30), position + query.length + 50), query);
          } else note.innerHTML = page.excerpt;
          link.append(note);
        }
        row.append(link);
        list.append(row);
      }
      results.replaceChildren();
      if (list.childElementCount) {
        const summary = document.createElement('p');
        summary.className = 'search-summary';
        summary.textContent = `找到 ${list.childElementCount} 篇经历`;
        results.append(summary, list);
      }
      else results.textContent = '没有找到匹配内容';
      syncScrollHint();
    } catch (error) {
      if (id !== requestId) return;
      results.textContent = '全文搜索暂不可用，请刷新页面后重试。';
      console.error('Pagefind search failed', error);
    }
  });
  const renderView = () => {
    if (dialog.open) dialog.close();
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
    year.value = history.state?.year || 'all';
    year.dispatchEvent(new Event('yearsync'));
    renderFilters();
  };
  year.addEventListener('change', () => {
    history.replaceState({...history.state, year: year.value}, '');
    renderFilters();
  });
  const indexPath = path => path.replace(/index\.html$/, '');
  document.addEventListener('click', event => {
    const link = event.target.closest('a[href]');
    if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || link.hasAttribute('download') || (link.target && link.target !== '_self')) return;
    const url = new URL(link.href);
    if (url.origin !== location.origin || indexPath(url.pathname) !== indexPath(location.pathname) || url.hash) return;
    event.preventDefault();
    if (url.href === location.href) {
      // Like the personal homepage: clicking the brand on the current home
      // document returns to the top instead of silently swallowing the click.
      if (link.matches('.brand, .mobile-brand')) {
        setMenu(false);
        window.scrollTo({
          top: 0,
          behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'
        });
      }
      return;
    }
    history.pushState({year: 'all'}, '', url);
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
