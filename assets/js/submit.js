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
    // Size each field to its wrapped placeholder, leaving room for the drag handle.
    // Never allow the handle to cover the placeholder when dragged upward.
    for (const control of controls.values()) {
      if (control.tagName !== 'TEXTAREA' || control.name === 'body') continue;
      const grip = make('button', '↘');
      grip.type = 'button';
      grip.className = 'textarea-grip';
      grip.setAttribute('aria-label', '拖动调整输入框高度');
      const holder = make('div');
      holder.className = 'textarea-holder';
      control.replaceWith(holder);
      holder.append(control, grip);
      let minimum = 0;
      let manuallyResized = false;
      const measure = () => {
        const probe = control.cloneNode();
        probe.value = '';
        probe.rows = 1;
        probe.style.height = 'auto';
        probe.style.minHeight = '0';
        probe.style.position = 'absolute';
        probe.style.visibility = 'hidden';
        probe.style.pointerEvents = 'none';
        probe.style.resize = 'none';
        holder.append(probe);
        // scrollHeight accounts for wrapped placeholder text and textarea padding.
        minimum = Math.ceil(probe.scrollHeight + 14);
        probe.remove();
        control.style.minHeight = minimum + 'px';
        if (!manuallyResized) control.style.height = minimum + 'px';
        else if (control.getBoundingClientRect().height < minimum) control.style.height = minimum + 'px';
      };
      measure();
      window.addEventListener('resize', measure);
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
        manuallyResized = true;
        control.style.height = Math.max(minimum, startHeight + event.clientY - startY) + 'px';
      });
      for (const name of ['pointerup', 'pointercancel']) grip.addEventListener(name, event => {
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
    const bodyControl = controls.get('body');
    const editorHost = make('div');
    editorHost.id = 'rich-editor';
    editorHost.className = 'rich-editor article-body';
    editorHost.hidden = true;
    bodyControl.after(editorHost);
    let richEditor = null;
    const editorStatus = make('small', '正在加载可视化编辑器…');
    editorStatus.className = 'field-hint';
    editorHost.after(editorStatus);
    import('./editor/editor.js').then(({ mountEditor }) => {
      richEditor = mountEditor(editorHost, bodyControl.value, markdown => {
        bodyControl.value = markdown;
        bodyControl.dispatchEvent(new Event('input', { bubbles: true }));
      });
      editorHost.hidden = false;
      bodyControl.hidden = true;
      bodyControl.required = false;
      editorStatus.textContent = '正文直接显示排版效果；内容保存为 Markdown 草稿。';
    }).catch(error => {
      console.error('Rich editor failed to initialize:', error?.stack || String(error));
      editorHost.remove();
      editorStatus.textContent = '可视化编辑器加载失败，请使用 Markdown 文本框。';
    });
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
        if (richEditor) richEditor.commands.clearContent(false);
        // Reset must not recreate a stale draft through the editor update callback.
        try { sessionStorage.removeItem(draftKey); } catch {}
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
        if (field.name === 'body' && richEditor) continue;
        control.setCustomValidity(field.required && !control.value.trim() ? '请填写' + field.label : '');
      }
      if (richEditor && !bodyControl.value.trim()) {
        editorStatus.textContent = '请先填写经历正文。';
        richEditor.commands.focus();
        return;
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
      if (richEditor) body.innerHTML = richEditor.getHTML();
      else renderMarkdown(String(data.get('body') || ''), body);
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
