import { defineConfig } from 'vite';
export default defineConfig({
  build: {
    outDir: 'assets/js/editor',
    emptyOutDir: true,
    lib: { entry: 'src/editor.js', formats: ['es'], fileName: () => 'editor.js' },
    rollupOptions: { output: { inlineDynamicImports: true } },
  },
});
