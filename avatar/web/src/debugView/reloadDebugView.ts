import { IDebugView } from './iDebugView.js'

export class ReloadDebugView implements IDebugView {
    readonly name = 'Reload'

    acceptDiv(_div: HTMLDivElement): void {
        window.location.reload()
    }
}
