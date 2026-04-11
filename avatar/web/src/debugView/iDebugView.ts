export interface IDebugView {
    readonly name: string
    acceptDiv(div: HTMLDivElement): void
}
