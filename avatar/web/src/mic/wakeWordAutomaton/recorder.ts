import { MicData } from '../input/micData.js'
import { SoundBuffer } from '../core/soundBuffer.js'
import { Dispatcher } from '../../core/dispatcher.js'
import { Message, Envelop } from '../../core/message.js'

function buildWavHeader(sampleRate: number): Uint8Array {
    const buf = new ArrayBuffer(44)
    const v = new DataView(buf)
    const byteRate = sampleRate * 2  // 16-bit mono

    // RIFF chunk
    v.setUint8(0, 0x52); v.setUint8(1, 0x49); v.setUint8(2, 0x46); v.setUint8(3, 0x46)  // "RIFF"
    v.setUint32(4, 0, true)          // file size placeholder
    v.setUint8(8, 0x57); v.setUint8(9, 0x41); v.setUint8(10, 0x56); v.setUint8(11, 0x45) // "WAVE"

    // fmt chunk
    v.setUint8(12, 0x66); v.setUint8(13, 0x6D); v.setUint8(14, 0x74); v.setUint8(15, 0x20) // "fmt "
    v.setUint32(16, 16, true)        // chunk size
    v.setUint16(20, 1, true)         // PCM format
    v.setUint16(22, 1, true)         // mono
    v.setUint32(24, sampleRate, true)
    v.setUint32(28, byteRate, true)
    v.setUint16(32, 2, true)         // block align
    v.setUint16(34, 16, true)        // bits per sample

    // data chunk
    v.setUint8(36, 0x64); v.setUint8(37, 0x61); v.setUint8(38, 0x74); v.setUint8(39, 0x61) // "data"
    v.setUint32(40, 0, true)         // data size placeholder

    return new Uint8Array(buf)
}

export class Recorder {
    private startBuffer: SoundBuffer
    private normalBuffer: SoundBuffer
    private filename: string | null = null
    private chunkIndex = 0
    private initPromise: Promise<void> | null = null
    private pendingWrites: Promise<void>[] = []
    private dispatcher: Dispatcher
    private baseUrl: string

    constructor({
        startBufferLength,
        normalBufferLength = 0.3,
        dispatcher,
        baseUrl,
    }: {
        startBufferLength: number,
        normalBufferLength?: number,
        dispatcher: Dispatcher,
        baseUrl: string,
    }) {
        this.dispatcher = dispatcher
        this.baseUrl = baseUrl.replace(/\/+$/, '')
        this.startBuffer = new SoundBuffer({ maxTimeSeconds: startBufferLength })
        this.normalBuffer = new SoundBuffer({ maxTimeSeconds: normalBufferLength, allowOverfill: true })
    }

    observe(micData: MicData): void {
        this.startBuffer.add(micData)
    }

    private async _sendChunk(filename: string, index: number, data: Uint8Array): Promise<void> {
        const url = `${this.baseUrl}/streaming/append/${encodeURIComponent(filename)}?chunk_index=${index}`
        const resp = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/octet-stream' },
            body: data,
        })
        if (!resp.ok) throw new Error(`[Recorder] append chunk ${index} failed: ${resp.status}`)
    }

    private _writeBuffer(buffer: SoundBuffer): void {
        if (buffer.isEmpty || !this.filename) return
        const pcm = buffer.toPcm()
        const bytes = new Uint8Array(pcm.buffer, pcm.byteOffset, pcm.byteLength)
        const index = this.chunkIndex++
        const filename = this.filename
        const p = this._sendChunk(filename, index, bytes)
            .catch(err => console.error('[Recorder] chunk write failed:', err))
        this.pendingWrites.push(p)
        buffer.clear()
    }

    private async _firstWrite(sampleRate: number): Promise<void> {
        const filename = `recording-${crypto.randomUUID()}.wav`
        this.filename = filename

        const beginResp = await fetch(
            `${this.baseUrl}/streaming/begin-writing/${encodeURIComponent(filename)}`,
            { method: 'POST' }
        )
        if (!beginResp.ok) throw new Error(`[Recorder] begin-writing failed: ${beginResp.status}`)

        // Send WAV header as chunk 0 — awaited so it lands on disk before SoundStreamingStartEvent fires
        await this._sendChunk(filename, this.chunkIndex++, buildWavHeader(sampleRate))

        // Flush pre-roll — awaited for the same reason
        if (!this.startBuffer.isEmpty) {
            const pcm = this.startBuffer.toPcm()
            await this._sendChunk(filename, this.chunkIndex++,
                new Uint8Array(pcm.buffer, pcm.byteOffset, pcm.byteLength))
            this.startBuffer.clear()
        }

        this.dispatcher.push(new Message('SoundStreamingStartEvent', new Envelop(), { file_id: filename }))
    }

    private _write(micData: MicData): void {
        this.normalBuffer.add(micData)
        if (this.normalBuffer.isFull) {
            this._writeBuffer(this.normalBuffer)
        }
    }

    async write(micData: MicData): Promise<void> {
        if (this.initPromise === null) {
            this.initPromise = this._firstWrite(micData.sampleRate)
        }
        await this.initPromise
        this._write(micData)
    }

    async commit(): Promise<void> {
        if (!this.filename) return
        if (!this.normalBuffer.isEmpty) {
            this._writeBuffer(this.normalBuffer)
        }
        await Promise.all(this.pendingWrites)
        const filename = this.filename
        const commitResp = await fetch(
            `${this.baseUrl}/streaming/commit/${encodeURIComponent(filename)}`,
            { method: 'POST' }
        )
        if (!commitResp.ok) throw new Error(`[Recorder] commit failed: ${commitResp.status}`)
        this.dispatcher.push(new Message('SoundStreamingEndEvent', new Envelop(), { file_id: filename, success: true }))
        this._cleanup()
    }

    async cancel(): Promise<void> {
        if (!this.filename) { this._cleanup(); return }
        const filename = this.filename
        this._cleanup()
        await fetch(
            `${this.baseUrl}/streaming/delete/${encodeURIComponent(filename)}`,
            { method: 'POST' }
        ).catch(err => console.error('[Recorder] cancel failed:', err))
        this.dispatcher.push(new Message('SoundStreamingEndEvent', new Envelop(), { file_id: filename, success: false }))
    }

    private _cleanup(): void {
        this.filename = null
        this.chunkIndex = 0
        this.initPromise = null
        this.pendingWrites = []
    }
}
