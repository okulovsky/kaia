import { IWebcam } from './iWebcam.js'

export class FakeWebcam implements IWebcam {
    private _width: number
    private _height: number
    private _whitePercentagePerStep: number
    private _frameIndex = 0
    private _running = false

    constructor({ width = 320, height = 240, whitePercentagePerStep }: {
        width?: number
        height?: number
        whitePercentagePerStep: number
    }) {
        this._width = width
        this._height = height
        this._whitePercentagePerStep = whitePercentagePerStep
    }

    async start(): Promise<void> {
        this._running = true
        this._frameIndex = 0
    }

    stop(): void {
        this._running = false
    }

    isRunning(): boolean {
        return this._running
    }

    read(): HTMLCanvasElement | null {
        if (!this._running) return null

        const k = this._frameIndex
        const totalPixels = this._width * this._height
        let whitePixels = Math.round(k * this._whitePercentagePerStep * totalPixels)

        if (whitePixels > totalPixels) {
            this._frameIndex = 0
            whitePixels = 0
        } else {
            this._frameIndex++
        }

        const canvas = document.createElement('canvas')
        canvas.width = this._width
        canvas.height = this._height
        const ctx = canvas.getContext('2d')!
        const imageData = ctx.createImageData(this._width, this._height)

        for (let i = 0; i < totalPixels; i++) {
            const isWhite = i < whitePixels
            const val = isWhite ? 255 : 0
            imageData.data[i * 4] = val
            imageData.data[i * 4 + 1] = val
            imageData.data[i * 4 + 2] = val
            imageData.data[i * 4 + 3] = 255
        }

        ctx.putImageData(imageData, 0, 0)
        return canvas
    }
}
