(() => {
  const form = document.querySelector('#submission-form');
  const category = document.querySelector('#category');
  const fields = document.querySelector('#dynamic-fields');
  const preview = document.querySelector('#preview');
  const previewText = document.querySelector('#preview-text');
  const button = document.querySelector('#preview-button');
  const draftStatus = document.querySelector('#draft-status');
  const draftKey = 'uem-draft-v1';
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
      if (field.type === 'textarea') control.rows = 2;
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
    // Touch browsers do not expose the native textarea resize grip.
    for (const control of controls.values()) {
      if (control.tagName !== 'TEXTAREA') continue;
      const grip = make('button', '↘');
      grip.type = 'button';
      grip.className = 'textarea-grip';
      grip.setAttribute('aria-label', '拖动调整' + control.previousElementSibling?.textContent + '高度');
      const holder = make('div');
      holder.className = 'textarea-holder';
      control.replaceWith(holder);
      holder.append(control, grip);
      let startY = 0, startHeight = 0;
      grip.addEventListener('pointerdown', event => {
        if (event.button !== 0) return;
        startY = event.clientY;
        startHeight = control.getBoundingClientRect().height;
        grip.setPointerCapture(event.pointerId);
        event.preventDefault();
      });
      grip.addEventListener('pointermove', event => {
        if (!grip.hasPointerCapture(event.pointerId)) return;
        control.style.height = Math.max(76, startHeight + event.clientY - startY) + 'px';
      });
      grip.addEventListener('pointerup', event => {
        if (grip.hasPointerCapture(event.pointerId)) grip.releasePointerCapture(event.pointerId);
      });
      grip.addEventListener('pointercancel', event => {
        if (grip.hasPointerCapture(event.pointerId)) grip.releasePointerCapture(event.pointerId);
      });
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
    try {
      const draft = JSON.parse(sessionStorage.getItem(draftKey) || 'null');
      if (draft) {
        for (const [name, value] of Object.entries(draft)) {
          const control = name === 'category' ? category : controls.get(name);
          if (control && name !== 'contact' && typeof value === 'string') control.value = value;
        }
        draftStatus.textContent = '已恢复当前标签页的草稿（不含联系方式），尚未提交。';
      }
    } catch {}
    updateCategory();
    const save = () => {
      hidePreview();
      try {
        const values = Object.fromEntries(new FormData(form));
        delete values.contact;
        sessionStorage.setItem(draftKey, JSON.stringify(values));
      } catch { draftStatus.textContent = '无法暂存草稿，请自行备份。'; }
    };
    form.addEventListener('input', save);
    form.addEventListener('change', save);
    form.addEventListener('reset', () => {
      hidePreview();
      try { sessionStorage.removeItem(draftKey); } catch {}
      draftStatus.textContent = '草稿已清空，尚未提交。';
      requestAnimationFrame(() => {
        updateCategory();
          });
    });
    const addInline = (parent, source) => {
      const parts = source.split(/(\*\*[^*]+\*\*|\[[^\]]+\]\(https?:\/\/[^ )]+\))/g);
      for (const part of parts) {
        if (part.startsWith('**') && part.endsWith('**')) parent.append(make('strong', part.slice(2, -2)));
        else if (/^\[[^\]]+\]\(https?:\/\/[^ )]+\)$/.test(part)) {
          const match = /^\[([^\]]+)\]\((https?:\/\/[^ )]+)\)$/.exec(part);
          const link = make('a', match[1]);
          link.href = match[2]; link.rel = 'noopener noreferrer'; link.target = '_blank';
          parent.append(link);
        } else parent.append(document.createTextNode(part));
      }
    };
    const renderMarkdown = (source, target) => {
      target.replaceChildren();
      let list = null;
      for (const line of source.split(/\r?\n/)) {
        const text = line.trim();
        if (!text) { list = null; continue; }
        const heading = /^(#{2,3})\s+(.+)$/.exec(text);
        const item = /^([-*]|[0-9]+\.)\s+(.+)$/.exec(text);
        let node;
        if (heading) { list = null; node = make('h' + heading[1].length); addInline(node, heading[2]); target.append(node); }
        else if (item) {
          const kind = /^[0-9]/.test(item[1]) ? 'ol' : 'ul';
          if (!list || list.tagName.toLowerCase() !== kind) { list = make(kind); target.append(list); }
          node = make('li'); addInline(node, item[2]); list.append(node);
        } else {
          list = null;
          node = make(text.startsWith('> ') ? 'blockquote' : 'p');
          addInline(node, text.startsWith('> ') ? text.slice(2) : text);
          target.append(node);
        }
      }
    };
    button.addEventListener('click', () => {
      for (const field of schema.fields) {
        const control = controls.get(field.name);
        control.setCustomValidity(field.required && !control.value.trim() ? '请填写' + field.label : '');
      }
      if (!form.reportValidity()) return;
      const data = new FormData(form);
      const selected = schema.categories.find(item => item.id === data.get('category'));
      if (!selected) return;
      previewText.replaceChildren(make('h3', String(data.get('title')).trim()));
      const metadata = make('dl');
      metadata.className = 'preview-meta';
      metadata.append(make('dt', '分享方向'), make('dd', selected.label));
      for (const field of schema.fields) {
        if (field.name === 'title' || field.name === 'body') continue;
        const value = String(data.get(field.name) || '').trim();
        if (value) metadata.append(make('dt', field.label), make('dd', value + (field.suffix ? ' ' + field.suffix : '')));
      }
      previewText.append(metadata, make('h3', '经历正文'));
      const body = make('div');
      body.className = 'article-body';
      renderMarkdown(String(data.get('body') || ''), body);
      previewText.append(body);
      preview.hidden = false;
      preview.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
    });
    for (const control of controls.values()) control.addEventListener('input', () => control.setCustomValidity(''));

  }).catch(() => {
    fields.textContent = '表单加载失败，请刷新重试。';
    button.disabled = true;
  });
})();
