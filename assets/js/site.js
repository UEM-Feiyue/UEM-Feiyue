(() => {
  const root = document.documentElement;
  let saved;
  try { saved = localStorage.getItem('uem-theme'); } catch {}
  if (saved === 'dark' || saved === 'light') root.dataset.theme = saved;
  const theme = document.querySelector('#theme-toggle');
  theme?.addEventListener('click', () => {
    const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    try { localStorage.setItem('uem-theme', next); } catch {}
  });

  const sidebar = document.querySelector('#sidebar');
  const toggle = document.querySelector('#menu-toggle');
  const scrim = document.querySelector('#scrim');
  const close = () => { sidebar.classList.remove('open'); toggle.setAttribute('aria-expanded', 'false'); toggle.setAttribute('aria-label', '打开导航'); scrim.hidden = true; };
  toggle?.addEventListener('click', () => {
    const open = sidebar.classList.toggle('open');
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? '关闭导航' : '打开导航');
    scrim.hidden = !open;
  });
  scrim?.addEventListener('click', close);
  sidebar?.querySelectorAll('a').forEach(a => a.addEventListener('click', close));
  document.addEventListener('keydown', event => { if (event.key === 'Escape') close(); });

  const el = (tag, className, content) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (content != null) node.textContent = content;
    return node;
  };
  const base = new URL('../..', document.currentScript.src).href.replace(/\/$/, '') + '/';
  const load = async path => {
    const response = await fetch(base + path);
    if (!response.ok) throw new Error('Could not load ' + path);
    return response.json();
  };
  Promise.all([load('data/schema.json'), load('data/articles.json')]).then(([schema, articles]) => {
    const nav = document.querySelector('#category-nav');
    const grid = document.querySelector('#category-grid');
    const selected = new URLSearchParams(location.search).get('category');
    const activeCategory = schema.categories.some(item => item.id === selected) ? selected : 'all';
    const current = schema.categories.find(item => item.id === activeCategory);
    const heading = document.querySelector('#stories-heading');
    const intro = document.querySelector('#category-intro');
    if (heading && current) heading.textContent = current.label + '经历';
    if (intro && current) intro.textContent = current.description + '，阅读同学的经验分享。';
    const year = document.querySelector('#year-filter');
    const search = document.querySelector('#search');
    const results = document.querySelector('#articles');
    const count = document.querySelector('#results-count');
    for (const item of schema.categories) {
      const a = el('a', '', item.label);
      a.href = base + '?category=' + encodeURIComponent(item.id);
      a.dataset.category = item.id;
      nav.append(a);
      if (grid) {
        const card = el('a', 'category-card');
        card.href = a.href;
        card.append(el('span', 'category-name', item.label), el('span', 'category-desc', item.description), el('span', 'category-arrow', '↗'));
        grid.append(card);
      }

    }
    if (!results) return;

    const years = [...new Set(articles.map(item => String(item.year || '')).filter(Boolean))].sort().reverse();
    years.forEach(value => { const option = el('option', '', value); option.value = value; year.append(option); });
    const render = () => {
      const query = search.value.trim().toLocaleLowerCase();
      const visible = articles.filter(item => (activeCategory === 'all' || item.category === activeCategory) && (year.value === 'all' || String(item.year) === year.value) && [item.title, item.author, item.major, item.destination, item.excerpt, ...(item.tags || [])].join(' ').toLocaleLowerCase().includes(query));
      results.replaceChildren();
      count.textContent = visible.length + ' 篇经历' + (visible.some(item => item.demo) ? ' · 含演示内容' : '');
      if (!visible.length) {
        const empty = el('div', 'empty-state');
        empty.append(el('h3', '', articles.length ? '暂时没有匹配的经历' : '故事即将从这里开始'), el('p', '', articles.length ? '试试其他关键词或筛选条件。' : '第一篇真实分享，期待由你写下。'));
        const link = el('a', 'text-link', '分享我的经历 ↗');
        link.href = 'submit.html';
        empty.append(link);
        results.append(empty);
      } else for (const item of visible) {
        const article = el('article', 'article-item');
        const link = el('a', '', item.title);
        link.href = base + item.url;
        const heading = el('h3');
        heading.append(link);
        if (item.demo) article.append(el('span', 'demo-badge', '演示'));
        article.append(el('p', 'article-meta', [schema.categories.find(c => c.id === item.category)?.label, item.year && item.year + ' 届', item.major].filter(Boolean).join(' · ')), heading, el('p', 'article-excerpt', item.excerpt || ''));
        const more = el('a', 'article-more', '阅读全文 ');
        more.href = base + item.url;
        more.append(el('span', 'arrow-icon', '↗'));
        article.append(more);
        results.append(article);
      }
      nav.querySelectorAll('[data-category]').forEach(a => a.removeAttribute('aria-current'));
      nav.querySelector('[data-category="' + activeCategory + '"]')?.setAttribute('aria-current', 'page');
    };
    search.addEventListener('input', render);
    year.addEventListener('change', render);

    render();
  }).catch(() => {
    const results = document.querySelector('#articles');
    if (results) results.textContent = '内容加载失败，请刷新页面重试。';
  });
})();
