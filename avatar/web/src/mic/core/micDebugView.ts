import { IDebugView } from '../../debugView/iDebugView.js'
import { Dispatcher, Handler } from '../../core/dispatcher.js'
import { Message, Envelop } from '../../core/message.js'

export class MicDebugView implements IDebugView {
    readonly name = 'MicDebugView'
    private baseUrl: string
    private dispatcher: Dispatcher
    private silenceLevel: number | null = null
    private soundLevelHandler: Handler | null = null

    constructor({ baseUrl, dispatcher }: { baseUrl: string, dispatcher: Dispatcher }) {
        this.baseUrl = baseUrl
        this.dispatcher = dispatcher
    }

    private emitSetSilenceLevel(delta: number): void {
        if (this.silenceLevel === null) return
        this.silenceLevel = Math.round((this.silenceLevel + delta) * 1000) / 1000
        this.dispatcher.push(new Message('SetSilenceLevelCommand', new Envelop(), {
            level: this.silenceLevel,
        }))
    }

    release(): void {
        if (this.soundLevelHandler) {
            this.dispatcher.unsubscribe('SoundLevelReport', this.soundLevelHandler)
            this.soundLevelHandler = null
        }
        this.silenceLevel = null
    }

    acceptDiv(div: HTMLDivElement): void {
        this.silenceLevel = null

        const iframe = document.createElement('iframe')
        const base = this.baseUrl.replace(/\/+$/, '')
        iframe.src = `${base}/audio_dashboard/dash/`
        iframe.style.width = '100%'
        iframe.style.height = '100%'
        iframe.style.border = 'none'

        const controls = document.createElement('div')
        controls.style.display = 'flex'
        controls.style.gap = '6px'
        controls.style.padding = '4px'

        const buttons: HTMLButtonElement[] = []

        const makeButton = (delta: number) => {
            const btn = document.createElement('button')
            btn.textContent = (delta > 0 ? '+' : '') + delta.toFixed(delta === 0.1 || delta === -0.1 ? 1 : 2)
            btn.disabled = true
            btn.addEventListener('click', () => this.emitSetSilenceLevel(delta))
            buttons.push(btn)
            return btn
        }

        controls.appendChild(makeButton(-0.1))
        controls.appendChild(makeButton(-0.01))
        controls.appendChild(makeButton(+0.01))
        controls.appendChild(makeButton(+0.1))

        this.soundLevelHandler = this.dispatcher.subscribe('SoundLevelReport', async (msg) => {
            this.silenceLevel = msg.payload.silence_level
            for (const btn of buttons) btn.disabled = false
        })

        div.style.display = 'flex'
        div.style.flexDirection = 'column'
        div.appendChild(controls)
        div.appendChild(iframe)
    }
}
