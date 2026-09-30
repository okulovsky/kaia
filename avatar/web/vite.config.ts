import { defineConfig } from 'vite'
import { readFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { dirname, resolve } from 'node:path'

const require = createRequire(import.meta.url)
const engineRoot = dirname(require.resolve('openwakeword-wasm-browser/package.json'))
const ortDist = dirname(require.resolve('onnxruntime-web'))

export default defineConfig({
    // All URLs also work when the backend overrides --outDir.
    base: '/frontend/scripts/',
    resolve: {
        alias: [{ find: /^onnxruntime-web$/, replacement: resolve(ortDist, 'ort.wasm.bundle.min.mjs') }],
    },
    worker: { format: 'es' },
    plugins: [{
        name: 'openwakeword-assets',
        generateBundle() {
            for (const name of ['melspectrogram.onnx', 'embedding_model.onnx', 'silero_vad.onnx', 'alexa_v0.1.onnx']) {
                this.emitFile({ type: 'asset', fileName: `openwakeword/models/${name}`, source: readFileSync(resolve(engineRoot, 'models', name)) })
            }
            for (const name of ['ort-wasm-simd-threaded.mjs', 'ort-wasm-simd-threaded.wasm']) {
                this.emitFile({ type: 'asset', fileName: `openwakeword/ort/${name}`, source: readFileSync(resolve(ortDist, name)) })
            }
        },
    }],
    build: {
        outDir: 'frontend/scripts',
        emptyOutDir: true,
        rollupOptions: {
            preserveEntrySignatures: 'exports-only',
            input: {
                'kaia-frontend': 'src/index.ts',
                'kaldi-wake-word-detector': 'src/mic/kaldiWakeWordDetector.ts',
                'bumblebee-wake-word-detector': 'src/mic/bumblebeeWakeWordDetector.ts',
                'open-wake-word-detector': 'src/mic/openWakeWordDetector.ts',
            },
            output: {
                entryFileNames: '[name].js',
                chunkFileNames: '_chunks/[name]-[hash].js',
                format: 'es',
            }
        }
    }
})
