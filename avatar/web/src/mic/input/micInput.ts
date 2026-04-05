import { IAudioInput } from './iAudioInput.js'
import { MicData } from './micData.js'

// Runs inside AudioWorklet: forwards float32 frames to the main thread as-is.
const MIC_PROCESSOR_CODE = `
class MicProcessor extends AudioWorkletProcessor {
    process(inputs, outputs, parameters) {
        const channel = inputs[0] && inputs[0][0]
        if (channel) {
            const copy = new Float32Array(channel)
            this.port.postMessage(copy.buffer, [copy.buffer])
        }
        return true
    }
}
registerProcessor('mic-processor', MicProcessor)
`

export class MicInput implements IAudioInput {
    private frameSize: number
    private sampleRate = 0
    private queue: Float32Array[] = []
    private pending: number[] = []
    private audioContext?: AudioContext
    private workletNode?: AudioWorkletNode
    private stream?: MediaStream
    private running = false
    private startTimeMs: number | null = null
    private samplesProduced = 0

    constructor({ frameSize = 512 }: { frameSize?: number } = {}) {
        this.frameSize = frameSize
    }

    async start(): Promise<void> {
        this.stream = await navigator.mediaDevices.getUserMedia({
            audio: { echoCancellation: true, noiseSuppression: true, channelCount: 1 }
        })

        // @ts-expect-error webkit prefix fallback
        const ctx = new (window.AudioContext || window.webkitAudioContext)() as AudioContext
        this.audioContext = ctx
        this.sampleRate = ctx.sampleRate
        console.log(`[MicInput] AudioContext sample rate: ${ctx.sampleRate}`)

        const blob = new Blob([MIC_PROCESSOR_CODE], { type: 'application/javascript' })
        const url = URL.createObjectURL(blob)
        await ctx.audioWorklet.addModule(url)
        URL.revokeObjectURL(url)

        this.workletNode = new AudioWorkletNode(ctx, 'mic-processor', { channelCount: 1 })
        this.workletNode.port.onmessage = (e: MessageEvent<ArrayBuffer>) => {
            const incoming = new Float32Array(e.data)
            for (let i = 0; i < incoming.length; i++) {
                this.pending.push(incoming[i])
            }
            while (this.pending.length >= this.frameSize) {
                this.queue.push(new Float32Array(this.pending.splice(0, this.frameSize)))
            }
        }

        const source = ctx.createMediaStreamSource(this.stream)
        source.connect(this.workletNode)
        this.startTimeMs = Date.now()
        this.samplesProduced = 0
        this.running = true
    }

    read(): MicData | null {
        const buffer = this.queue.shift()
        if (buffer === undefined) return null
        const sr = this.sampleRate || 48000
        const micTimestamp = this.startTimeMs! + (this.samplesProduced / sr) * 1000
        this.samplesProduced += buffer.length
        return { sampleRate: sr, buffer, micTimestamp }
    }

    stop(): void {
        this.workletNode?.disconnect()
        this.stream?.getTracks().forEach(t => t.stop())
        this.audioContext?.close()
        this.running = false
    }

    isRunning(): boolean {
        return this.running
    }
}
