import { MicData } from '../input/micData.js'

export class SoundBuffer {
    maxTimeSeconds: number
    isFull = false
    private allowOverfill: boolean
    private queue: MicData[] = []
    private totalSamples = 0
    private totalLevelSum = 0
    private sampleRate: number | null = null

    constructor({ maxTimeSeconds, allowOverfill = false }: { maxTimeSeconds: number, allowOverfill?: boolean }) {
        this.maxTimeSeconds = maxTimeSeconds
        this.allowOverfill = allowOverfill
    }

    get isEmpty(): boolean {
        return this.totalSamples === 0
    }

    get frames(): readonly MicData[] {
        return this.queue
    }

    add(data: MicData): void {
        if (this.sampleRate !== null && this.sampleRate !== data.sampleRate) {
            this.clear()
        }
        this.sampleRate = data.sampleRate
        this.queue.push(data)
        this.totalSamples += data.buffer.length
        this.totalLevelSum += data.levelSum

        const maxSamples = Math.floor(this.maxTimeSeconds * this.sampleRate)
        if (this.totalSamples >= maxSamples) {
            if (!this.allowOverfill) {
                // Remove entries from the front as long as the buffer remains full without them
                while (this.queue.length > 1 && this.totalSamples - this.queue[0].buffer.length >= maxSamples) {
                    const ejected = this.queue.shift()!
                    this.totalSamples -= ejected.buffer.length
                    this.totalLevelSum -= ejected.levelSum
                }
            }
            this.isFull = true
        }
    }

    getLevel(): number {
        return this.totalSamples > 0 ? this.totalLevelSum / this.totalSamples : 0
    }

    toPcm(): Int16Array {
        const result = new Int16Array(this.totalSamples)
        let offset = 0
        for (const entry of this.queue) {
            for (let i = 0; i < entry.buffer.length; i++) {
                const s = Math.max(-1, Math.min(1, entry.buffer[i]))
                result[offset++] = s < 0 ? Math.round(s * 32768) : Math.round(s * 32767)
            }
        }
        return result
    }

    clear(): void {
        this.queue = []
        this.totalSamples = 0
        this.totalLevelSum = 0
        this.isFull = false
        this.sampleRate = null
    }
}
