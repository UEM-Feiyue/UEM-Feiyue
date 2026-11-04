(() => {
  const form = document.querySelector('#submission-form');
  const category = document.querySelector('#category');
  const fields = document.querySelector('#dynamic-fields');
  const preview = document.querySelector('#preview');
  const previewText = document.querySelector('#preview-text');
  const make = (tag, text) => { const node = document.createElement(tag); if (text != null) node.textContent = text; return node; };
  fetch('data/schema.json').then(r => { if (!r.ok) throw Error('schema'); return r.json(); }).then(schema => {
    for (const item of schema.categories) {
      const option = make('option', item.label);
      option.value = item.id;
      category.append(option);
    }
    for (const field of schema.fields) {
      const wrapper = make('div');
      wrapper.className = 'field';
      const label = make('label', field.label + (field.required ? ' *' : ''));
      label.htmlFor = field.name;
      const control = make(field.type === 'textarea' ? 'textarea' : 'input');
      control.id = field.name;
      control.name = field.name;
      control.required = Boolean(field.required);
      if (field.type !== 'textarea') control.type = field.type;
      if (field.maxLength) control.maxLength = field.maxLength;
      if (field.placeholder) control.placeholder = field.placeholder;
      if (field.type === 'textarea') control.rows = field.name === 'body' ? 12 : 3;
      wrapper.append(label, control);
      fields.append(wrapper);
    }
    document.querySelector('#preview-button').addEventListener('click', () => {
      if (!form.reportValidity()) return;
      const data = new FormData(form);
      const title = String(data.get('title') || '');
      const lines = ['# ' + title, '', '方向：' + schema.categories.find(c => c.id === data.get('category')).label];
      for (const field of schema.fields) {
        if (field.name === 'title') continue;
        const value = String(data.get(field.name) || '').trim();
        if (value) lines.push('', field.label + '：', value);
      }
      previewText.textContent = lines.join('\n');
      preview.hidden = false;
      preview.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' });
    });
    form.addEventListener('reset', () => { preview.hidden = true; });
  }).catch(() => { fields.textContent = '表单加载失败，请刷新重试。'; });
})();
