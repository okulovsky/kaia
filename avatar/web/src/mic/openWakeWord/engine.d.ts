// The npm package has no declarations. Internal streaming methods are used only
// in worker.ts; recheck this contract when upgrading the pinned package.
declare module 'openwakeword-wasm-browser' {
    export default class WakeWordEngine {
        constructor(options: {
            keywords: string[], baseAssetUrl: string, ortWasmPath: string,
            detectionThreshold: number, cooldownMs: number, debug: boolean,
        })
        load(): Promise<void>
        on(event: 'detect', handler: (event: { keyword: string, score: number }) => void): () => void
        on(event: 'error', handler: (error: unknown) => void): () => void
        _processChunk(chunk: Float32Array): Promise<void>
        _resetState(): void
    }
}
