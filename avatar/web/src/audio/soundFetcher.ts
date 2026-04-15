import { Message } from '../core/message.js'

export function soundUrl(base: string, msg: Message): string {
    if (msg.message_type.endsWith('SystemSoundCommand')) {
        return `${base}/frontend/system-sounds/${encodeURIComponent(msg.payload.sound_name)}.wav`
    }
    if (msg.message_type.endsWith('SoundCommand')) {
        return `${base}/cache/open/${encodeURIComponent(msg.payload.file_id)}`
    }
    throw new Error(`[soundFetcher] unsupported message type: ${msg.message_type}`)
}

export async function fetchSound(base: string, msg: Message): Promise<ArrayBuffer> {
    const url = soundUrl(base, msg)
    const resp = await fetch(url)
    if (!resp.ok) throw new Error(`[soundFetcher] fetch failed ${url}: ${resp.status}`)
    return resp.arrayBuffer()
}

export function wavDurationSeconds(buffer: ArrayBuffer): number {
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
            const numSamples = chunkSize / 2  // 16-bit mono
            return numSamples / sampleRate
        }
        offset += 8 + chunkSize
    }
    throw new Error('[soundFetcher] no data chunk found in WAV')
}
