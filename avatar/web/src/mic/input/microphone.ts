import { IMicrophone } from './iMicrophone.js'
import { MicData } from './micData.js'

// Runs inside AudioWorklet: downsamples from the AudioContext's native rate to
// targetSampleRate and posts frameSize-sample Float32Array frames to the main thread.
const MIC_PROCESSOR_CODE = `
class MicProcessor extends AudioWorkletProcessor {
    constructor(options) {
        super()
        const { targetSampleRate, frameSize } = options.processorOptions
        this._ratio = sampleRate / targetSampleRate
        this._frameSize = frameSize
        this._buf = new Float32Array(8192)
        this._len = 0
    }

    process(inputs, outputs, parameters) {
        const channel = inputs[0] && inputs[0][0]
        if (!channel) return true

        if (this._len + channel.length > this._buf.length) {
            const next = new Float32Array(this._buf.length * 2)
            next.set(this._buf.subarray(0, this._len))
            this._buf = next
        }
        this._buf.set(channel, this._len)
        this._len += channel.length

        while (this._len >= this._frameSize) {
            let frame
            if (this._ratio === 1) {
                frame = this._buf.slice(0, this._frameSize)
                this._buf.copyWithin(0, this._frameSize, this._len)
                this._len -= this._frameSize
            } else {
                if (this._len / this._ratio < this._frameSize) break
                frame = new Float32Array(this._frameSize)
                let inputIndex = 0
                for (let out = 0; out < this._frameSize; out++) {
                    const limit = Math.min(this._len, (out + 1) * this._ratio)
                    let sum = 0, count = 0
                    while (inputIndex < limit) {
                        sum += this._buf[inputIndex++]
                        count++
                    }
                    frame[out] = count > 0 ? sum / count : 0
                }
                this._buf.copyWithin(0, inputIndex, this._len)
                this._len -= inputIndex
            }
            this.port.postMessage(frame.buffer, [frame.buffer])
        }

        return true
    }
}
registerProcessor('mic-processor', MicProcessor)
`

export class Microphone implements IMicrophone {
    private frameSize: number
    private sampleRate = 0
    private queue: Float32Array[] = []
    private audioContext?: AudioContext
    private workletNode?: AudioWorkletNode
    private stream?: MediaStream
    private running = false
    private startTimeMs: number | null = null
    private samplesProduced = 0

    constructor({ frameSize = 512, sampleRate = 16000 }: { frameSize?: number, sampleRate?: number } = {}) {
        this.frameSize = frameSize
        this.sampleRate = sampleRate
    }

    async start(): Promise<void> {
        this.stream = await navigator.mediaDevices.getUserMedia({
            audio: { echoCancellation: true, noiseSuppression: true, channelCount: 1 }
        })

        // @ts-expect-error webkit prefix fallback
        const ctx = new (window.AudioContext || window.webkitAudioContext)() as AudioContext
        this.audioContext = ctx
        console.log(`[Microphone] AudioContext native rate: ${ctx.sampleRate}, target rate: ${this.sampleRate}`)

        const blob = new Blob([MIC_PROCESSOR_CODE], { type: 'application/javascript' })
        const url = URL.createObjectURL(blob)
        await ctx.audioWorklet.addModule(url)
        URL.revokeObjectURL(url)

        this.workletNode = new AudioWorkletNode(ctx, 'mic-processor', {
            channelCount: 1,
            processorOptions: { targetSampleRate: this.sampleRate, frameSize: this.frameSize },
        })
        this.workletNode.port.onmessage = (e: MessageEvent<ArrayBuffer>) => {
            this.queue.push(new Float32Array(e.data))
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
        if (!this.sampleRate) return null
        const micTimestamp = this.startTimeMs! + (this.samplesProduced / this.sampleRate) * 1000
        this.samplesProduced += buffer.length
        return new MicData(this.sampleRate, buffer, micTimestamp)
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
