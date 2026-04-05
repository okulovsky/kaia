import { MicData } from '../input/micData.js'

export class SoundBuffer {
    maxTimeSeconds: number
    sampleRate: number | null = null
    buffer: number[] = []
    isFull = false
    private allowOverfill: boolean

    constructor({ maxTimeSeconds, allowOverfill = false }: { maxTimeSeconds: number, allowOverfill?: boolean }) {
        this.maxTimeSeconds = maxTimeSeconds
        this.allowOverfill = allowOverfill
    }

    add(data: MicData): void {
        if (this.sampleRate !== data.sampleRate) {
            this.sampleRate = data.sampleRate
            this.clear()
        }
        for (let i = 0; i < data.buffer.length; i++) {
            this.buffer.push(data.buffer[i])
        }
        const maxSamples = Math.floor(this.maxTimeSeconds * this.sampleRate!)
        if (this.buffer.length >= maxSamples) {
            if (!this.allowOverfill) {
                this.buffer = this.buffer.slice(this.buffer.length - maxSamples)
            }
            this.isFull = true
        }
    }

    toPcm(): Int16Array {
        const result = new Int16Array(this.buffer.length)
        for (let i = 0; i < this.buffer.length; i++) {
            const s = Math.max(-1, Math.min(1, this.buffer[i]))
            result[i] = s < 0 ? Math.round(s * 32768) : Math.round(s * 32767)
        }
        return result
    }

    clear(): void {
        this.buffer = []
        this.isFull = false
    }
}
