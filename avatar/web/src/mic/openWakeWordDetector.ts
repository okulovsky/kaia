import { Message, Envelop, Dispatcher } from '../core/index.js'
import type { MicData } from './input/index.js'
import type { IWakeWordDetector } from './wakeWordAutomaton/index.js'
import type { ILoadingScreenComponent } from '../loadingScreen/index.js'
import type { WorkerRequest, WorkerResponse } from './openWakeWord/protocol.js'

const SAMPLE_RATE = 16000
const FRAME_SIZE = 1280
const MAX_PENDING_CHUNKS = 25 // Bound latency/memory to two seconds of audio.

export class OpenWakeWordDetector implements ILoadingScreenComponent, IWakeWordDetector {
    readonly name = 'OpenWakeWordDetector (Alexa)'
    private worker?: Worker
    private initialization?: Promise<void>
    private initialized = false
    private failure?: Error
    private frame = new Float32Array(FRAME_SIZE)
    private position = 0
    private chunks: Float32Array[] = []
    private busy = false
    private generation = 0
    private expectedTimestamp?: number
    private detected: string | null = null

    constructor (private readonly options: {
        dispatcher: Dispatcher,
        assetBaseUrl?: string,
        detectionThreshold?: number,
        cooldownMs?: number,
        debug?: boolean,
    }) {}

    initialize (): Promise<void> {
        if (this.initialization) return this.initialization
        this.initialization = new Promise((resolve, reject) => {
            const worker = new Worker(new URL('./openWakeWord/worker.ts', import.meta.url), { type: 'module' })
            this.worker = worker
            const fail = (error: Error) => {
                this.failure = error
                this.initialized = false
                this.chunks = []
                worker.terminate()
                reject(error)
                console.error('[OpenWakeWord]', error)
            }
            worker.onerror = event => fail(new Error(event.message || 'OpenWakeWord worker failed'))
            worker.onmessage = (event: MessageEvent<WorkerResponse>) => {
                const message = event.data
                if (message.type === 'error') {
                    fail(new Error(message.message))
                } else if (message.type === 'ready') {
                    this.initialized = true
                    resolve()
                } else {
                    this.busy = false
                    if (message.generation === this.generation && message.keyword) {
                        this.detected = message.keyword
                    }
                    this.sendNext()
                }
            }
            const assetBaseUrl = new URL(
                this.options.assetBaseUrl ?? '/frontend/scripts/openwakeword', window.location.href,
            ).href.replace(/\/+$/, '')
            this.post({
                type: 'initialize', assetBaseUrl,
                detectionThreshold: this.options.detectionThreshold ?? 0.5,
                cooldownMs: this.options.cooldownMs ?? 2000,
                debug: this.options.debug ?? false,
            })
        })
        return this.initialization
    }

    private post (message: WorkerRequest): void {
        this.worker!.postMessage(message)
    }

    private resetStream (): void {
        this.generation++
        this.position = 0
        this.chunks = []
        this.detected = null
    }

    private sendNext (): void {
        if (this.busy || this.failure) return
        const chunk = this.chunks.shift()
        if (!chunk) return
        this.busy = true
        this.post({ type: 'process', chunk, generation: this.generation })
    }

    detect (micData: MicData): boolean {
        if (this.failure) throw this.failure
        if (!this.initialized) return false
        if (micData.sampleRate !== SAMPLE_RATE) throw new Error('OpenWakeWord requires 16000 Hz PCM')

        // Recording/playback phases can interrupt the stream. Do not concatenate
        // unrelated audio or deliver a detection left over from before the gap.
        if (this.expectedTimestamp !== undefined && Math.abs(micData.micTimestamp - this.expectedTimestamp) > 1) {
            this.resetStream()
        }
        this.expectedTimestamp = micData.micTimestamp + micData.buffer.length / SAMPLE_RATE * 1000

        const keyword = this.detected
        this.detected = null
        for (const sample of micData.buffer) {
            this.frame[this.position++] = sample
            if (this.position === FRAME_SIZE) {
                if (this.chunks.length >= MAX_PENDING_CHUNKS) {
                    this.resetStream()
                    console.warn('[OpenWakeWord] Inference fell behind; resetting audio history')
                }
                this.chunks.push(this.frame)
                this.frame = new Float32Array(FRAME_SIZE)
                this.position = 0
            }
        }
        this.sendNext()
        if (keyword) {
            this.options.dispatcher.push(new Message('WakeWordEvent', new Envelop(), { word: keyword }))
            return true
        }
        return false
    }
}
