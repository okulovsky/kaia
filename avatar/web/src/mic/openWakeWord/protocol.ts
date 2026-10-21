export type WorkerRequest =
    | { type: 'initialize', assetBaseUrl: string, modelUrl?: string, keyword: string, detectionThreshold: number, cooldownMs: number, debug: boolean }
    | { type: 'process', chunk: Float32Array, generation: number }

export type WorkerResponse =
    | { type: 'ready' }
    | { type: 'result', generation: number, keyword: string | null, score?: number }
    | { type: 'error', message: string }
