import { IDebugView } from '../../debugView/iDebugView.js'

export class MicDebugView implements IDebugView {
    readonly name = 'MicDebugView'
    constructor(private baseUrl: string) {}

    acceptDiv(div: HTMLDivElement): void {
        const iframe = document.createElement('iframe')
        const base = this.baseUrl.replace(/\/+$/, '')
        iframe.src = `${base}/audio_dashboard/dash/`
        iframe.style.width = '100%'
        iframe.style.height = '100%'
        iframe.style.border = 'none'
        div.appendChild(iframe)
    }
}
