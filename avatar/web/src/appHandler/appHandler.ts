import { IPausable } from '../core/iPausable.js'
import { Dispatcher } from '../core/dispatcher.js'

export class AppHandler {
    private _div: HTMLDivElement
    private _pausables: IPausable[]
    private _iframe: HTMLIFrameElement | null = null

    constructor(div: HTMLDivElement, pausables: IPausable[], dispatcher: Dispatcher) {
        this._div = div
        this._pausables = pausables

        const closeBtn = document.createElement('button')
        closeBtn.textContent = 'Close'
        closeBtn.className = 'app-overlay-close'
        closeBtn.addEventListener('click', () => void this._close())
        div.appendChild(closeBtn)

        div.style.display = 'none'

        dispatcher.subscribe('OpenApp', async (msg) => {
            await this._open(msg.payload?.url as string)
        })
    }

    private async _open(url: string): Promise<void> {
        if (this._iframe) return

        await Promise.all(this._pausables.map(p => p.pause()))

        const iframe = document.createElement('iframe')
        iframe.src = url
        this._div.appendChild(iframe)
        this._iframe = iframe

        this._div.style.display = 'flex'
    }

    private async _close(): Promise<void> {
        if (this._iframe) {
            this._iframe.remove()
            this._iframe = null
        }
        this._div.style.display = 'none'

        await Promise.all(this._pausables.map(p => p.resume()))
    }
}
