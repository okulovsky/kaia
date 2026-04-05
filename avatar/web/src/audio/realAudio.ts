import { Dispatcher } from '../core/dispatcher.js'
import { Message, Envelop } from '../core/message.js'
import { soundUrl, wavDurationSeconds } from './soundFetcher.js'

export class RealAudio {
    private dispatcher: Dispatcher
    private context: AudioContext | null = null
    private currentSource: AudioBufferSourceNode | null = null
    private currentMsg: Message | null = null
    private silentTimeoutId: ReturnType<typeof setTimeout> | null = null
    private generation = 0
    private silent: boolean
    private acceleration: number

    constructor({ dispatcher, baseUrl, silent = false, acceleration = 1 }: {
        dispatcher: Dispatcher,
        baseUrl: string,
        silent?: boolean,
        acceleration?: number,
    }) {
        this.dispatcher = dispatcher
        this.silent = silent
        this.acceleration = acceleration
        if (!silent) {
            this.context = new AudioContext()
        }
        const base = baseUrl.replace(/\/+$/, '')
        dispatcher.subscribe('SoundCommand', (msg) => {
            if (msg.message_type.endsWith('SystemSoundCommand')) return Promise.resolve()
            return this._handle(msg, soundUrl(base, msg))
        })
        dispatcher.subscribe('SystemSoundCommand', (msg) => this._handle(msg, soundUrl(base, msg)))
    }

    private _interrupt(): void {
        if (this.currentMsg === null) return
        const oldMsg = this.currentMsg
        this.currentMsg = null
        if (this.currentSource !== null) {
            this.currentSource.onended = null
            this.currentSource.stop()
            this.currentSource = null
        }
        if (this.silentTimeoutId !== null) {
            clearTimeout(this.silentTimeoutId)
            this.silentTimeoutId = null
        }
        this.dispatcher.push(
            new Message('SoundConfirmation', new Envelop(), { terminated: true })
                .asConfirmationFor(oldMsg)
        )
    }

    private _confirm(msg: Message, terminated: boolean, error?: string): void {
        this.dispatcher.push(
            new Message('SoundConfirmation', new Envelop(), {
                terminated,
                error: error ?? null,
            }).asConfirmationFor(msg)
        )
    }

    private async _handle(msg: Message, url: string): Promise<void> {
        this._interrupt()

        const gen = ++this.generation

        let arrayBuffer: ArrayBuffer
        try {
            const resp = await fetch(url)
            if (!resp.ok) {
                const error = `fetch failed ${url}: ${resp.status}`
                console.error(`[RealAudio] ${error}`)
                if (gen === this.generation) this._confirm(msg, false, error)
                return
            }
            arrayBuffer = await resp.arrayBuffer()
        } catch (e) {
            const error = `fetch error: ${e}`
            console.error(`[RealAudio] ${error}`)
            if (gen === this.generation) this._confirm(msg, false, error)
            return
        }

        if (gen !== this.generation) return

        this.currentMsg = msg

        if (this.silent) {
            let duration: number
            try {
                duration = wavDurationSeconds(arrayBuffer)
            } catch (e) {
                const error = `wavDurationSeconds failed: ${e}`
                console.error(`[RealAudio] ${error}`)
                this.currentMsg = null
                this._confirm(msg, false, error)
                return
            }
            this.silentTimeoutId = setTimeout(() => {
                if (this.currentMsg === msg) {
                    this.currentMsg = null
                    this.silentTimeoutId = null
                    this._confirm(msg, false)
                }
            }, duration * 1000 / this.acceleration)
            return
        }

        let audioBuffer: AudioBuffer
        try {
            audioBuffer = await this.context!.decodeAudioData(arrayBuffer)
        } catch (e) {
            const error = `decode error: ${e}`
            console.error(`[RealAudio] ${error}`)
            if (gen === this.generation) {
                this.currentMsg = null
                this._confirm(msg, false, error)
            }
            return
        }

        if (gen !== this.generation) return

        if (this.context!.state === 'suspended') {
            await this.context!.resume()
        }

        const source = this.context!.createBufferSource()
        source.buffer = audioBuffer
        source.connect(this.context!.destination)
        this.currentSource = source

        source.onended = () => {
            if (this.currentMsg === msg) {
                this.currentSource = null
                this.currentMsg = null
                this._confirm(msg, false)
            }
        }

        source.start()
    }
}
