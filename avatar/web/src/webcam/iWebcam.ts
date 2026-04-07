export interface IWebcam {
    start(): Promise<void>
    stop(): void
    isRunning(): boolean
    read(): HTMLCanvasElement | null
}
