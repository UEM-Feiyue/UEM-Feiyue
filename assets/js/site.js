(() => {
  const root = document.documentElement;
  let saved;
  try { saved = localStorage.getItem('uem-theme'); } catch {}
  if (saved === 'dark' || saved === 'light') root.dataset.theme = saved;
  document.querySelectorAll('#theme-toggle, #theme-toggle-mobile').forEach(theme => theme.addEventListener('click', () => {
    const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    try { localStorage.setItem('uem-theme', next); } catch {}
  }));

  const sidebar = document.querySelector('#sidebar');
  const toggle = document.querySelector('#menu-toggle');
  const mobile = matchMedia('(max-width: 900px)');
  const closeMenu = (restoreFocus = false) => {
    sidebar.classList.remove('open');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-label', '打开导航');
    if (restoreFocus && mobile.matches) toggle.focus();
  };
  toggle?.addEventListener('click', () => {
    const open = sidebar.classList.toggle('open');
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? '关闭导航' : '打开导航');
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

  const el = (tag, className, content) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (content != null) node.textContent = content;
    return node;
  };
  const base = new URL('../../', document.currentScript.src).href;
  const load = async path => {
    const response = await fetch(base + path);
    if (!response.ok) throw new Error('Could not load ' + path);
    return response.json();
  };
  // One footer implementation for home, archives, submission and generated articles.
  const footer = document.querySelector('[data-site-footer]');
  const footerLinks = footer && el('nav', 'footer-links');
  if (footer) {
    const inner = el('div', 'footer-inner');
    const grid = el('div', 'footer-grid');
    const identity = el('div', 'footer-brand');
    const brand = el('a', 'footer-brand-link');
    brand.href = base;
    const logo = el('img', 'footer-logo');
    logo.src = base + 'assets/images/favicon-横版.png';
    logo.alt = '应急管理大学飞跃手册';
    logo.width = 1226;
    logo.height = 285;
    brand.append(logo);
    identity.append(brand, el('p', '', '记录升学与职业路上的真实经历，让经验被看见，让后来者少走弯路。'));
    const linksSection = el('div');
    linksSection.append(el('h2', 'footer-title', '探索'));
    footerLinks.setAttribute('aria-label', '页脚导航');
    const addFooterLink = (label, href) => {
      const link = el('a', '', label);
      link.href = base + href;
      footerLinks.append(link);
    };
    addFooterLink('全部经历', '?view=all');
    linksSection.append(footerLinks);
    const bottom = el('div', 'footer-bottom');
    bottom.append(el('span', '', 'UEM Feiyue · 由同学共同维护'));
    const github = el('a', '', 'GitHub · 项目仓库');
    github.href = 'https://github.com/UEM-Feiyue/UEM-Feiyue.github.io';
    github.target = '_blank';
    github.rel = 'noopener noreferrer';
    bottom.append(github);
    grid.append(identity, linksSection);
    inner.append(grid, bottom);
    footer.append(inner);
  }
  const nav = document.querySelector('#category-nav');
  const params = new URLSearchParams(location.search);
  const selected = params.get('category');
  const archive = document.querySelector('#archive-section');
  const isHome = Boolean(archive) && !selected && params.get('view') !== 'all';
  document.querySelector('.page')?.classList.toggle('is-home', isHome);
  document.querySelector('#home-intro')?.toggleAttribute('hidden', !isHome);
  document.querySelector('#archive-intro')?.toggleAttribute('hidden', isHome);
  if (archive) archive.hidden = isHome;
  if (archive && !isHome) {
    nav.querySelector('[data-view="home"]')?.removeAttribute('aria-current');
    nav.querySelector('[data-category="all"]')?.setAttribute('aria-current', 'page');
  }

  load('data/schema.json').then(schema => {
    const activeCategory = schema.categories.some(item => item.id === selected) ? selected : 'all';
    const current = schema.categories.find(item => item.id === activeCategory);
    const heading = document.querySelector('#stories-heading');
    const intro = document.querySelector('#category-intro');
    if (heading) heading.textContent = current ? current.label + '经历' : '全部经历';
    if (intro) intro.textContent = current ? current.description + '，阅读同学的经验分享。' : '按方向浏览同学分享的升学与职业经验。';
    if (footerLinks) {
      for (const item of schema.categories) {
        const link = el('a', '', item.label);
        link.href = base + '?category=' + encodeURIComponent(item.id);
        footerLinks.append(link);
      }
      const contribute = el('a', '', '投稿分享');
      contribute.href = base + 'submit.html';
      footerLinks.append(contribute);
    }
    for (const item of schema.categories) {
      const link = el('a', '', item.label);
      link.href = base + '?category=' + encodeURIComponent(item.id);
      link.dataset.category = item.id;
      nav.insertBefore(link, nav.querySelector('.nav-contribute'));
    }
    if (archive && !isHome && current) {
      nav.querySelector('[data-category="all"]')?.removeAttribute('aria-current');
      nav.querySelector('[data-category="' + activeCategory + '"]')?.setAttribute('aria-current', 'page');
    }
    if (!archive) return;
    return load('data/articles.json').then(articles => {
      const year = document.querySelector('#year-filter');
      const search = document.querySelector('#search');
      const results = document.querySelector('#articles');
      const count = document.querySelector('#results-count');
      const years = [...new Set(articles.map(item => String(item.year || '')).filter(Boolean))].sort().reverse();
      years.forEach(value => {
        const option = el('option', '', value);
        option.value = value;
        year.append(option);
      });
      const render = () => {
        const query = search.value.trim().toLocaleLowerCase();
        const visible = articles.filter(item =>
          (activeCategory === 'all' || item.category === activeCategory) &&
          (year.value === 'all' || String(item.year) === year.value) &&
          [item.title, item.author, item.major, item.destination, item.excerpt, ...(item.tags || [])]
            .join(' ').toLocaleLowerCase().includes(query)
        );
        results.replaceChildren();
        count.textContent = visible.length + ' 篇经历' + (visible.some(item => item.demo) ? ' · 含演示内容' : '');
        if (!visible.length) {
          const empty = el('div', 'empty-state');
          empty.append(
            el('h3', '', articles.length ? '暂时没有匹配的经历' : '故事即将从这里开始'),
            el('p', '', articles.length ? '试试其他关键词或筛选条件。' : '第一篇真实分享，期待由你写下。')
          );
          const link = el('a', 'text-link', '分享我的经历');
          link.href = base + 'submit.html';
          link.append(el('span', 'link-arrow'));
          empty.append(link);
          results.append(empty);
          return;
        }
        for (const item of visible) {
          const article = el('article', 'article-item');
          const link = el('a', '', item.title);
          link.href = base + item.url;
          const title = el('h3');
          title.append(link);
          if (item.demo) article.append(el('span', 'demo-badge', '演示'));
          article.append(
            el('p', 'article-meta', [schema.categories.find(c => c.id === item.category)?.label, item.year && item.year + ' 届', item.major].filter(Boolean).join(' · ')),
            title,
            el('p', 'article-excerpt', item.excerpt || '')
          );
          const more = el('a', 'article-more', '阅读全文');
          more.href = link.href;
          more.append(el('span', 'link-arrow'));
          article.append(more);
          results.append(article);
        }
      };
      search.addEventListener('input', render);
      year.addEventListener('change', render);
      render();
    });
  }).catch(() => {
    const results = document.querySelector('#articles');
    if (results) {
      results.textContent = '内容加载失败，请稍后刷新重试。';
      document.querySelector('#archive-section').hidden = false;
    }
  });
})();
