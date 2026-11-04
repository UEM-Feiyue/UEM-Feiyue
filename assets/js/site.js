(() => {
  const root = document.documentElement;
  const saved = localStorage.getItem('uem-theme');
  if (saved === 'dark' || saved === 'light') root.dataset.theme = saved;
  const theme = document.querySelector('#theme-toggle');
  theme?.addEventListener('click', () => {
    const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    localStorage.setItem('uem-theme', next);
  });

  const sidebar = document.querySelector('#sidebar');
  const toggle = document.querySelector('#menu-toggle');
  const scrim = document.querySelector('#scrim');
  const close = () => { sidebar.classList.remove('open'); toggle.setAttribute('aria-expanded', 'false'); scrim.hidden = true; };
  toggle?.addEventListener('click', () => {
    const open = sidebar.classList.toggle('open');
    toggle.setAttribute('aria-expanded', String(open));
    scrim.hidden = !open;
  });
  scrim?.addEventListener('click', close);
  document.addEventListener('keydown', event => { if (event.key === 'Escape') close(); });

  const el = (tag, className, content) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (content != null) node.textContent = content;
    return node;
  };
  const load = async path => {
    const response = await fetch(path);
    if (!response.ok) throw new Error('Could not load ' + path);
    return response.json();
  };
  Promise.all([load('data/schema.json'), load('data/articles.json')]).then(([schema, articles]) => {
    const nav = document.querySelector('#category-nav');
    const grid = document.querySelector('#category-grid');
    const select = document.querySelector('#category-filter');
    const year = document.querySelector('#year-filter');
    const search = document.querySelector('#search');
    const results = document.querySelector('#articles');
    const count = document.querySelector('#results-count');
    for (const item of schema.categories) {
      const a = el('a', '', item.label);
      a.href = './?category=' + encodeURIComponent(item.id);
      a.dataset.category = item.id;
      nav.append(a);
      if (grid) {
        const card = el('a', 'category-card');
        card.href = a.href;
        card.append(el('span', 'category-name', item.label), el('span', 'category-desc', item.description), el('span', 'category-arrow', '↗'));
        grid.append(card);
      }
      if (select) {
        const option = el('option', '', item.label);
        option.value = item.id;
        select.append(option);
      }
    }
    if (!results) return;
    const params = new URLSearchParams(location.search);
    const selected = params.get('category');
    if (schema.categories.some(item => item.id === selected)) select.value = selected;
    const years = [...new Set(articles.map(item => String(item.year || '')).filter(Boolean))].sort().reverse();
    years.forEach(value => { const option = el('option', '', value); option.value = value; year.append(option); });
    const render = () => {
      const query = search.value.trim().toLocaleLowerCase();
      const visible = articles.filter(item => (select.value === 'all' || item.category === select.value) && (year.value === 'all' || String(item.year) === year.value) && [item.title, item.author, item.major, item.destination, item.excerpt, ...(item.tags || [])].join(' ').toLocaleLowerCase().includes(query));
      results.replaceChildren();
      count.textContent = visible.length + ' 篇经历';
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
        link.href = item.url;
        const heading = el('h3');
        heading.append(link);
        article.append(el('p', 'article-meta', [schema.categories.find(c => c.id === item.category)?.label, item.year && item.year + ' 届', item.major].filter(Boolean).join(' · ')), heading, el('p', 'article-excerpt', item.excerpt || ''));
        results.append(article);
      }
      nav.querySelectorAll('[data-category]').forEach(a => a.removeAttribute('aria-current'));
      nav.querySelector('[data-category="' + select.value + '"]')?.setAttribute('aria-current', 'page');
    };
    search.addEventListener('input', render);
    year.addEventListener('change', render);
    select.addEventListener('change', () => {
      const url = new URL(location.href);
      if (select.value === 'all') url.searchParams.delete('category');
      else url.searchParams.set('category', select.value);
      history.replaceState(null, '', url);
      render();
    });
    render();
  }).catch(() => {
    const results = document.querySelector('#articles');
    if (results) results.textContent = '内容加载失败，请刷新页面重试。';
  });
})();
