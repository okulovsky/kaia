import { Dispatcher } from '../core/dispatcher.js'
import { Message, Envelop } from '../core/message.js'

export class RealAudio {
    private dispatcher: Dispatcher
    private baseUrl: string
    private context: AudioContext
    private currentSource: AudioBufferSourceNode | null = null
    private currentMsg: Message | null = null
    private generation = 0

    constructor({ dispatcher, baseUrl }: { dispatcher: Dispatcher, baseUrl: string }) {
        this.dispatcher = dispatcher
        this.baseUrl = baseUrl
        this.context = new AudioContext()
        const base = baseUrl.replace(/\/+$/, '')
        dispatcher.subscribe('SoundCommand', (msg) =>
            this._handle(msg, `${base}/cache/open/${encodeURIComponent(msg.payload.file_id)}`)
        )
        dispatcher.subscribe('SystemSoundCommand', (msg) =>
            this._handle(msg, `${base}/frontend/system-sounds/${encodeURIComponent(msg.payload.sound_name)}.wav`)
        )
    }

    private async _handle(msg: Message, url: string): Promise<void> {
        // Interrupt currently playing audio
        if (this.currentSource !== null) {
            const oldSource = this.currentSource
            const oldMsg = this.currentMsg!
            this.currentSource = null
            this.currentMsg = null
            oldSource.onended = null  // prevent natural-end handler from firing
            oldSource.stop()
            this.dispatcher.push(
                new Message('SoundConfirmation', new Envelop(), { terminated: true })
                    .asConfirmationFor(oldMsg)
            )
        }

        const gen = ++this.generation

        // Fetch audio bytes
        let arrayBuffer: ArrayBuffer
        try {
            const resp = await fetch(url)
            if (!resp.ok) {
                console.error(`[RealAudio] fetch failed ${url}: ${resp.status}`)
                return
            }
            arrayBuffer = await resp.arrayBuffer()
        } catch (e) {
            console.error('[RealAudio] fetch error:', e)
            return
        }

        // Bail if another command arrived while we were fetching
        if (gen !== this.generation) return

        // Decode
        let audioBuffer: AudioBuffer
        try {
            audioBuffer = await this.context.decodeAudioData(arrayBuffer)
        } catch (e) {
            console.error('[RealAudio] decode error:', e)
            return
        }

        if (gen !== this.generation) return

        if (this.context.state === 'suspended') {
            await this.context.resume()
        }

        const source = this.context.createBufferSource()
        source.buffer = audioBuffer
        source.connect(this.context.destination)
        this.currentSource = source
        this.currentMsg = msg

        source.onended = () => {
            if (this.currentMsg === msg) {
                this.currentSource = null
                this.currentMsg = null
                this.dispatcher.push(
                    new Message('SoundConfirmation', new Envelop(), { terminated: false })
                        .asConfirmationFor(msg)
                )
            }
        }

        source.start()
    }
}
