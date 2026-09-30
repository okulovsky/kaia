import WakeWordEngine from 'openwakeword-wasm-browser'
import { env } from 'onnxruntime-web'
import type { WorkerRequest, WorkerResponse } from './protocol.js'

// Run in a dedicated worker without requiring COOP/COEP or SharedArrayBuffer.
env.wasm.numThreads = 1
env.wasm.proxy = false

let engine: WakeWordEngine
let generation = -1
let detected: string | null = null
let pipelineError: unknown = null

function respond (message: WorkerResponse): void {
    self.postMessage(message)
}

// The adapter sends at most one chunk at a time: ONNX sessions and recurrent
// state must never be used concurrently.
self.onmessage = async (event: MessageEvent<WorkerRequest>) => {
    try {
        const message = event.data
        if (message.type === 'initialize') {
            engine = new WakeWordEngine({
                keywords: ['alexa'],
                baseAssetUrl: `${message.assetBaseUrl}/models`,
                ortWasmPath: `${message.assetBaseUrl}/ort/`,
                detectionThreshold: message.detectionThreshold,
                cooldownMs: message.cooldownMs,
                debug: message.debug,
            })
            engine.on('detect', ({ keyword }) => { detected = keyword })
            // The upstream VAD catches errors, so propagate those explicitly.
            engine.on('error', error => { pipelineError = error })
            await engine.load()
            respond({ type: 'ready' })
        } else {
            if (generation !== message.generation) {
                engine._resetState()
                generation = message.generation
            }
            detected = null
            pipelineError = null
            await engine._processChunk(message.chunk)
            if (pipelineError) throw pipelineError
            respond({ type: 'result', generation, keyword: detected })
        }
    } catch (error) {
        respond({ type: 'error', message: error instanceof Error ? error.message : String(error) })
    }
}
