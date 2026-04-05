import { defineConfig } from 'vite'

export default defineConfig({
    build: {
        outDir: 'frontend/scripts',
        emptyOutDir: true,
        rollupOptions: {
            preserveEntrySignatures: 'exports-only',
            input: {
                'index': 'src/index.ts',
                'wakeWordDetector': 'src/mic/wake_word_automaton/wakeWordDetector.ts',
            },
            output: {
                entryFileNames: '[name].js',
                chunkFileNames: '_chunks/[name]-[hash].js',
                format: 'es',
            }
        }
    }
})
