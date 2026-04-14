import { IDebugView } from './iDebugView.js'

export class DebugViewController {
    private registrations: IDebugView[] = []
    private open = false
    private activeView: IDebugView | null = null

    constructor(
        private settingsButton: HTMLElement,
        private div: HTMLDivElement,
    ) {
        settingsButton.addEventListener('click', () => this._onSettings())
    }

    register(view: IDebugView): void {
        this.registrations.push(view)
    }

    private _releaseActive(): void {
        if (this.activeView) {
            this.activeView.release()
            this.activeView = null
        }
    }

    private _onSettings(): void {
        if (this.open) {
            this._releaseActive()
            this.div.innerHTML = ''
            this.div.style.display = 'none'
            this.open = false
        } else {
            this.div.innerHTML = ''
            this.div.style.display = 'block'
            for (const view of this.registrations) {
                const btn = document.createElement('button')
                btn.textContent = view.name
                btn.className = 'debug-button-component'
                btn.addEventListener('click', () => {
                    this._releaseActive()
                    this.div.innerHTML = ''
                    view.acceptDiv(this.div)
                    this.activeView = view
                })
                this.div.appendChild(btn)
            }
            this.open = true
        }
    }
}
