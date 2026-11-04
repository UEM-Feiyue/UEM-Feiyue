(() => {
  const form = document.querySelector('#submission-form');
  const category = document.querySelector('#category');
  const fields = document.querySelector('#dynamic-fields');
  const preview = document.querySelector('#preview');
  const previewText = document.querySelector('#preview-text');
  const button = document.querySelector('#preview-button');
  const make = (tag, text) => {
    const node = document.createElement(tag);
    if (text != null) node.textContent = text;
    return node;
  };
  fetch('data/schema.json').then(response => {
    if (!response.ok) throw new Error('Could not load schema');
    return response.json();
  }).then(schema => {
    for (const item of schema.categories) {
      const option = make('option', item.label);
      option.value = item.id;
      category.append(option);
    }
    category.required = true;
    const controls = new Map();
    for (const field of schema.fields) {
      const wrapper = make('div');
      wrapper.className = 'field';
      const label = make('label', field.label + (field.required ? ' *' : '（选填）'));
      label.htmlFor = field.name;
      const control = make(field.type === 'textarea' ? 'textarea' : 'input');
      control.id = field.name;
      control.name = field.name;
      control.required = Boolean(field.required);
      if (field.type !== 'textarea') control.type = field.type;
      if (field.maxLength) control.maxLength = field.maxLength;
      if (field.placeholder) control.placeholder = field.placeholder;
      if (field.inputMode) control.inputMode = field.inputMode;
      if (field.pattern) control.pattern = field.pattern;
      if (field.type === 'textarea') control.rows = field.name === 'body' ? 12 : 3;
      wrapper.append(label);
      if (field.suffix) {
        const inputRow = make('div');
        inputRow.className = 'input-suffix';
        inputRow.append(control, make('span', field.suffix));
        wrapper.append(inputRow);
      } else {
        wrapper.append(control);
      }
      if (field.hint) {
        const hint = make('small', field.hint);
        hint.className = 'field-hint';
        hint.id = field.name + '-hint';
        control.setAttribute('aria-describedby', hint.id);
        wrapper.append(hint);
      }
      fields.append(wrapper);
      controls.set(field.name, control);
    }
    const year = controls.get('year');
    year.addEventListener('input', () => {
      const clean = year.value.replace(/[^0-9]/g, '').slice(0, 4);
      if (year.value !== clean) year.value = clean;
    });
    const destination = controls.get('destination');
    const updateCategory = () => {
      const definition = schema.fields.find(field => field.name === 'destination');
      destination.placeholder = definition.placeholders[category.value] || '';
    };
    category.addEventListener('change', updateCategory);
    updateCategory();

    const hidePreview = () => { preview.hidden = true; };
    form.addEventListener('input', hidePreview);
    form.addEventListener('change', hidePreview);
    form.addEventListener('reset', () => {
      hidePreview();
      requestAnimationFrame(updateCategory);
    });
    button.addEventListener('click', () => {
      if (!form.reportValidity()) return;
      const data = new FormData(form);
      const title = String(data.get('title') || '').trim();
      const selected = schema.categories.find(item => item.id === data.get('category'));
      if (!selected) return;
      const lines = ['# ' + title, '', '分享方向：' + selected.label];
      for (const field of schema.fields) {
        if (field.name === 'title') continue;
        const value = String(data.get(field.name) || '').trim();
        if (value) lines.push('', field.label + '：', value + (field.suffix ? ' ' + field.suffix : ''));
      }
      previewText.textContent = lines.join('\n');
      preview.hidden = false;
      preview.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
    });
  }).catch(() => {
    fields.textContent = '表单加载失败，请刷新重试。';
    button.disabled = true;
  });
})();
