import { InferenceSession, Tensor } from 'onnxruntime-web'

/** The supplied OWW and Nano heads share OWW's [1,16,96] features.
 * Keep this streaming extractor consistent with evaluation_features.py:
 * PCM16 scale, 480-sample lookback, mel/10+2, one embedding per 80 ms.
 * Alexa continues to use the original npm engine in worker.ts.
 */
export class ComputerWakeWordEngine {
    private mel!: InferenceSession
    private embedding!: InferenceSession
    private head!: InferenceSession
    private vad!: InferenceSession
    private tail = new Float32Array(0)
    private melHistory = new Float32Array(76 * 32).fill(1)
    private embeddings = new Float32Array(16 * 96)
    private h: Tensor = new Tensor('float32', new Float32Array(128), [2, 1, 64])
    private c: Tensor = new Tensor('float32', new Float32Array(128), [2, 1, 64])
    private speechHangover = 0
    private steps = 0
    private lastDetectionStep = -Infinity

    constructor (private readonly options: {
        assetBaseUrl: string, modelUrl?: string, keyword: string,
        detectionThreshold: number, cooldownMs: number, debug: boolean,
    }) {
        if (!Number.isFinite(options.detectionThreshold) || options.detectionThreshold < 0 || options.detectionThreshold > 1) {
            throw new Error('Wake word threshold must be between 0 and 1')
        }
        if (!Number.isFinite(options.cooldownMs) || options.cooldownMs < 0) {
            throw new Error('Wake word cooldown must be a non-negative duration')
        }
    }

    async load (): Promise<void> {
        // Worker and WASM runtime stay in the build; only the selected head is
        // downloaded from /resources/open/WakeWordModels/....
        const base = `${this.options.assetBaseUrl}/models`
        this.mel = await this.loadSession(`${base}/melspectrogram.onnx`)
        this.embedding = await this.loadSession(`${base}/embedding_model.onnx`)
        this.vad = await this.loadSession(`${base}/silero_vad.onnx`)
        this.head = await this.loadSession(this.options.modelUrl!)
        const input = this.head.inputMetadata[0]
        if (!input.isTensor || input.type !== 'float32' || input.shape.length !== 3 ||
            input.shape[1] !== 16 || input.shape[2] !== 96 ||
            (typeof input.shape[0] === 'number' && input.shape[0] !== 1)) {
            throw new Error(`Unsupported wake word input: ${JSON.stringify(input)}; expected [1,16,96] float32`)
        }
        this.reset()
    }

    private async loadSession (url: string): Promise<InferenceSession> {
        try {
            const response = await fetch(url)
            if (!response.ok) throw new Error(`HTTP ${response.status}`)
            return await InferenceSession.create(await response.arrayBuffer(), { executionProviders: ['wasm'] })
        } catch (error) {
            throw new Error(`Cannot load wake word asset ${url}: ${String(error)}`)
        }
    }

    reset (): void {
        this.tail = new Float32Array(0)
        this.melHistory.fill(1)
        this.embeddings.fill(0)
        this.h = new Tensor('float32', new Float32Array(128), [2, 1, 64])
        this.c = new Tensor('float32', new Float32Array(128), [2, 1, 64])
        this.speechHangover = 0
        this.steps = 0
        this.lastDetectionStep = -Infinity
    }

    async process (chunk: Float32Array): Promise<{ score: number, keyword: string | null }> {
        if (chunk.length !== 1280) throw new Error('Computer models require 1280 samples per block')
        const pcm = new Float32Array(this.tail.length + chunk.length)
        pcm.set(this.tail)
        for (let i = 0; i < chunk.length; i++) {
            if (!Number.isFinite(chunk[i])) throw new Error('Non-finite microphone sample')
            pcm[this.tail.length + i] = Math.round(Math.max(-1, Math.min(32767 / 32768, chunk[i])) * 32768)
        }
        const melOut = await this.mel.run({
            [this.mel.inputNames[0]]: new Tensor('float32', pcm, [1, pcm.length]),
        })
        const values = melOut[this.mel.outputNames[0]].data as Float32Array
        // First block yields 5 frames, subsequent 1760-sample inputs yield 8.
        const expected = this.steps === 0 ? 5 * 32 : 8 * 32
        if (values.length !== expected) throw new Error(`Unexpected mel shape: ${values.length}`)
        this.melHistory.copyWithin(0, values.length)
        for (let i = 0; i < values.length; i++) {
            this.melHistory[this.melHistory.length - values.length + i] = values[i] / 10 + 2
        }
        this.tail = pcm.slice(-480)
        const embeddingOut = await this.embedding.run({
            [this.embedding.inputNames[0]]: new Tensor('float32', this.melHistory, [1, 76, 32, 1]),
        })
        const vector = embeddingOut[this.embedding.outputNames[0]].data as Float32Array
        if (vector.length !== 96) throw new Error(`Unexpected embedding size: ${vector.length}`)
        this.embeddings.copyWithin(0, 96)
        // Copy: ORT can reuse output buffers on the following run.
        this.embeddings.set(vector, this.embeddings.length - 96)
        const headOut = await this.head.run({
            [this.head.inputNames[0]]: new Tensor('float32', this.embeddings, [1, 16, 96]),
        })
        const output = headOut[this.head.outputNames[0]].data
        const rawScore = Number(output[0])
        if (output.length !== 1 || !Number.isFinite(rawScore) || rawScore < 0 || rawScore > 1) {
            throw new Error(`Invalid wake word output: ${rawScore}`)
        }
        const vadOut = await this.vad.run({ input: new Tensor('float32', chunk, [1, 1280]),
            sr: new Tensor('int64', BigInt64Array.of(16000n), []), h: this.h, c: this.c })
        this.h = vadOut.hn
        this.c = vadOut.cn
        const confidence = Number(vadOut.output.data[0])
        if (!Number.isFinite(confidence)) throw new Error('Invalid VAD output')
        this.speechHangover = confidence > 0.5 ? 12 : Math.max(0, this.speechHangover - 1)
        this.steps++
        // Unlike the Python SDK's random initial embeddings, start with zero
        // history and allow detections only after 16 real embeddings (1.28 s).
        const score = this.steps < 16 ? 0 : rawScore
        const detected = this.steps >= 16 && score >= this.options.detectionThreshold && this.speechHangover > 0 &&
            (this.steps - this.lastDetectionStep) * 80 >= this.options.cooldownMs
        if (detected) this.lastDetectionStep = this.steps
        if (this.options.debug) console.debug('[ComputerWakeWord]', {
            keyword: this.options.keyword, score, vad: confidence, detected,
        })
        return { score, keyword: detected ? this.options.keyword : null }
    }
}
