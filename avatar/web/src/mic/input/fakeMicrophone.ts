import { IMicrophone } from './iMicrophone.js'
import { MicData } from './micData.js'
import { Dispatcher } from '../../core/dispatcher.js'
import { Message, Envelop } from '../../core/message.js'

function parseWav(buffer: ArrayBuffer): { sampleRate: number, samples: Int16Array } {
    const view = new DataView(buffer)
    const sampleRate = view.getUint32(24, true)
    let offset = 12
    while (offset < view.byteLength - 8) {
        const chunkId = String.fromCharCode(
            view.getUint8(offset), view.getUint8(offset + 1),
            view.getUint8(offset + 2), view.getUint8(offset + 3)
        )
        const chunkSize = view.getUint32(offset + 4, true)
        if (chunkId === 'data') {
            const samples = new Int16Array(buffer.slice(offset + 8, offset + 8 + chunkSize))
            return { sampleRate, samples }
        }
        offset += 8 + chunkSize
    }
    throw new Error('No data chunk found in WAV')
}

export class FakeMicrophone implements IMicrophone {
    private frameSize: number
    private sampleRate: number
    private acceleration: number
    private currentBuffer: Float32Array | null = null
    private currentPosition = 0
    private dispatcher?: Dispatcher
    private pendingConfirmation: Message | null = null
    private pendingStartedEvent: string | null = null
    private startRealTimeMs: number | null = null
    private startMicTimeMs: number | null = null
    private samplesProduced = 0

    constructor({ sampleRate, frameSize = 512, acceleration = 1, dispatcher, baseUrl }: {
        sampleRate: number,
        frameSize?: number,
        acceleration?: number,
        dispatcher?: Dispatcher,
        baseUrl?: string,
    }) {
        this.sampleRate = sampleRate
        this.frameSize = frameSize
        this.acceleration = acceleration
        this.dispatcher = dispatcher

        if (dispatcher && baseUrl) {
            const base = baseUrl.replace(/\/+$/, '')
            dispatcher.subscribe('SoundInjectionCommand', async (msg) => {
                const fileId: string = msg.payload.file_id
                const resp = await fetch(`${base}/cache/open/${encodeURIComponent(fileId)}`)
                if (!resp.ok) {
                    console.error(`[FakeMicrophone] Failed to fetch ${fileId}: ${resp.status}`)
                    return
                }
                this.pendingConfirmation = msg
                this.pendingStartedEvent = fileId
                this.setSample(await resp.arrayBuffer())
            })
        }
    }

    setSample(wavBytes: ArrayBuffer): void {
        const { sampleRate, samples } = parseWav(wavBytes)
        this.sampleRate = sampleRate
        this.currentBuffer = new Float32Array(samples.length)
        for (let i = 0; i < samples.length; i++) {
            this.currentBuffer[i] = samples[i] / 32768
        }
        this.currentPosition = 0
    }

    isBufferEmpty(): boolean {
        if (this.currentBuffer === null) return true
        return this.currentPosition >= this.currentBuffer.length
    }

    start(): Promise<void> {
        return Promise.resolve()
    }

    stop(): void {}

    read(): MicData | null {
        const now = Date.now()
        if (this.startRealTimeMs === null) {
            this.startRealTimeMs = now
            this.startMicTimeMs = now
        }

        const elapsedRealSec = (now - this.startRealTimeMs) / 1000
        const samplesExpected = Math.floor(elapsedRealSec * this.sampleRate * this.acceleration)
        if (samplesExpected - this.samplesProduced < this.frameSize) return null

        const micTimestamp = this.startMicTimeMs! + (this.samplesProduced / this.sampleRate) * 1000
        this.samplesProduced += this.frameSize

        if (this.isBufferEmpty()) {
            return new MicData(this.sampleRate, new Float32Array(this.frameSize), micTimestamp)
        }

        if (this.pendingStartedEvent !== null && this.dispatcher) {
            this.dispatcher.push(new Message('SoundInjectionStartedEvent', new Envelop(), { file_id: this.pendingStartedEvent }))
            this.pendingStartedEvent = null
        }

        const end = Math.min(this.currentPosition + this.frameSize, this.currentBuffer!.length)
        const chunk = this.currentBuffer!.slice(this.currentPosition, end)
        this.currentPosition += this.frameSize

        if (this.isBufferEmpty() && this.dispatcher && this.pendingConfirmation) {
            const confirmation = new Message('Confirmation', new Envelop(), {})
                .asConfirmationFor(this.pendingConfirmation)
            this.pendingConfirmation = null
            this.dispatcher.push(confirmation)
        }

        if (chunk.length < this.frameSize) {
            const padded = new Float32Array(this.frameSize)
            padded.set(chunk)
            return new MicData(this.sampleRate, padded, micTimestamp)
        }
        return new MicData(this.sampleRate, chunk, micTimestamp)
    }

    isRunning(): boolean {
        return true
    }
}
