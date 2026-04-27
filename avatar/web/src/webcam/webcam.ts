import { IWebcam } from './iWebcam.js'
import { ILoadingScreenComponent } from '../loadingScreen/iLoadingScreenComponent.js'

export class Webcam implements IWebcam, ILoadingScreenComponent {
    readonly name = 'Webcam'
    private _width: number
    private _height: number
    private _video: HTMLVideoElement
    private _canvas: HTMLCanvasElement
    private _stream: MediaStream | null = null
    private _running = false

    constructor({ width = 320, height = 240 }: {
        width?: number
        height?: number
    } = {}) {
        this._width = width
        this._height = height

        this._video = document.createElement('video')
        this._video.autoplay = true
        this._video.muted = true;
        (this._video as any).playsInline = true

        this._canvas = document.createElement('canvas')
        this._canvas.width = width
        this._canvas.height = height
    }

    async initialize(): Promise<void> {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { width: { ideal: this._width }, height: { ideal: this._height } },
            audio: false,
        })
        this._stream = stream
        this._video.srcObject = stream

        if (this._video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) {
            await new Promise<void>((resolve) => {
                this._video.addEventListener('canplay', () => resolve(), { once: true })
            })
        }

        const playPromise = this._video.play()
        if (playPromise) {
            playPromise.catch(() => {})
        }
    }

    async start(): Promise<void> {
        this._running = true
    }

    stop(): void {
        this._stream?.getTracks().forEach(t => t.stop())
        this._running = false
    }

    isRunning(): boolean {
        return this._running
    }

    read(): HTMLCanvasElement | null {
        if (!this._running) return null
        const ctx = this._canvas.getContext('2d')!
        ctx.drawImage(this._video, 0, 0, this._width, this._height)
        return this._canvas
    }
}
