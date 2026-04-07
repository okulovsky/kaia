import { defineConfig } from 'vite'

export default defineConfig({
    build: {
        outDir: 'frontend/scripts',
        emptyOutDir: true,
        rollupOptions: {
            preserveEntrySignatures: 'exports-only',
            input: {
                'kaia-frontend': 'src/index.ts',
                'kaldi-wake-word-detector': 'src/mic/kaldiWakeWordDetector.ts',
            },
            output: {
                entryFileNames: '[name].js',
                chunkFileNames: '_chunks/[name]-[hash].js',
                format: 'es',
            }
        }
    }
})
