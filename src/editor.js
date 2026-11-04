import { Editor } from '@tiptap/core';
import StarterKit from '@tiptap/starter-kit';
import { Markdown } from '@tiptap/markdown';
import { Heading } from '@tiptap/extension-heading';

// Tiptap 3.10.1 calls Markdown parsers without binding the extension context.
const MarkdownHeading = Heading.extend({
  parseMarkdown: (token, helpers) => {
    const level = token.depth || 1;
    return level === 2 || level === 3
      ? helpers.createNode('heading', { level }, helpers.parseInline(token.tokens || []))
      : helpers.createNode('paragraph', undefined, helpers.parseInline(token.tokens || []));
  },
}).configure({ levels: [2, 3] });

export function mountEditor(host, markdown, onChange) {
  const toolbar = document.createElement('div');
  toolbar.className = 'rich-editor-toolbar';
  toolbar.setAttribute('role', 'toolbar');
  toolbar.setAttribute('aria-label', '正文排版');
  const surface = document.createElement('div');
  host.append(toolbar, surface);
  const editor = new Editor({
    element: surface,
    extensions: [StarterKit.configure({ heading: false, link: { openOnClick: false } }), MarkdownHeading, Markdown],
    content: markdown || '',
    contentType: 'markdown',
    editorProps: { attributes: { 'aria-label': '经历正文编辑区' } },
    onUpdate: ({ editor }) => onChange(editor.getMarkdown()),
  });
  for (const [label, command] of [
    ['正文', () => editor.chain().focus().setParagraph().run()],
    ['二级标题', () => editor.chain().focus().toggleHeading({ level: 2 }).run()],
    ['三级标题', () => editor.chain().focus().toggleHeading({ level: 3 }).run()],
    ['加粗', () => editor.chain().focus().toggleBold().run()],
    ['无序列表', () => editor.chain().focus().toggleBulletList().run()],
    ['有序列表', () => editor.chain().focus().toggleOrderedList().run()],
    ['引用', () => editor.chain().focus().toggleBlockquote().run()],
    ['链接', () => {
      const previous = editor.getAttributes('link').href || '';
      const value = window.prompt('输入 HTTPS 链接（留空可移除现有链接）', previous);
      if (value === null) return;
      if (!value.trim()) { editor.chain().focus().unsetLink().run(); return; }
      try {
        const url = new URL(value.trim());
        if (!['https:', 'http:'].includes(url.protocol)) throw new Error('invalid protocol');
        editor.chain().focus().extendMarkRange('link').setLink({ href: url.href }).run();
      } catch { window.alert('请填写有效的 HTTP 或 HTTPS 链接。'); }
    }],
    ['撤销', () => editor.chain().focus().undo().run()],
    ['重做', () => editor.chain().focus().redo().run()],
  ]) {
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = label;
    button.addEventListener('click', command);
    toolbar.append(button);
  }
  return editor;
}
