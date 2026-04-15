import type { ILoadingScreenComponent } from './iLoadingScreenComponent.js'

export class LoadingScreen {
    private div: HTMLElement
    private callback: () => void
    private readyCount = 0
    private errorCount = 0
    private total: number

    constructor(div: HTMLElement, components: ILoadingScreenComponent[], callback: () => void) {
        this.div = div
        this.callback = callback
        this.total = components.length

        div.style.display = 'block'
        div.innerHTML = ''

        components.forEach(component => {
            const name = component.name
            const row = document.createElement('div')
            row.textContent = `${name}: loading`
            div.appendChild(row)

            component.initialize()
                .then(() => {
                    row.textContent = `${name}: ready`
                    this.readyCount++
                    this._check()
                })
                .catch((err: unknown) => {
                    const msg = err instanceof Error ? err.message : String(err)
                    row.textContent = `${name}: ${msg}`
                    this.errorCount++
                    this._check()
                })
        })
    }

    private _check(): void {
        if (this.readyCount + this.errorCount < this.total) return
        if (this.errorCount === 0) {
            this.div.style.display = 'none'
            this.callback()
        }
    }
}
