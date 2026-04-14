import { IWebcam } from './iWebcam.js'
import { IDebugView } from '../debugView/iDebugView.js'
import { AvatarClient } from '../core/avatarClient.js'
import { Message } from '../core/message.js'

export class WebcamProcessor implements IDebugView {
    readonly name = 'WebcamProcessor'
    private _webcam: IWebcam
    private _rateMs: number
    private _threshold: number
    private _pixelThreshold: number
    private _client: AvatarClient
    private _baseUrl: string

    private _pixelSamplingStep: number
    private _storedCanvas: HTMLCanvasElement | null = null
    private _intervalId: ReturnType<typeof setInterval> | null = null

    private _debugDiv: HTMLDivElement | null = null
    private _imgCurrent: HTMLImageElement | null = null
    private _imgStored: HTMLImageElement | null = null
    private _imgDiff: HTMLImageElement | null = null

    constructor({ webcam, rateMs = 1000, threshold = 0.1, pixelThreshold = 30, pixelSamplingStep = 2, client, baseUrl }: {
        webcam: IWebcam
        rateMs?: number
        threshold?: number
        pixelThreshold?: number
        pixelSamplingStep?: number
        client: AvatarClient
        baseUrl: string
    }) {
        this._webcam = webcam
        this._rateMs = rateMs
        this._threshold = threshold
        this._pixelThreshold = pixelThreshold
        this._pixelSamplingStep = pixelSamplingStep
        this._client = client
        this._baseUrl = baseUrl.replace(/\/+$/, '')
    }

    async start(): Promise<void> {
        await this._webcam.start()
        this._intervalId = setInterval(() => { void this._tick() }, this._rateMs)
    }

    stop(): void {
        if (this._intervalId !== null) {
            clearInterval(this._intervalId)
            this._intervalId = null
        }
        this._webcam.stop()
    }

    private detectMovement(current: HTMLCanvasElement): { moved: boolean; diffCanvas: HTMLCanvasElement | null } {
        if (this._storedCanvas === null) {
            return { moved: true, diffCanvas: null }
        }

        const w = current.width
        const h = current.height
        const byteStep = this._pixelSamplingStep * 4

        const storedCtx = this._storedCanvas.getContext('2d')!
        const currentCtx = current.getContext('2d')!
        const img1 = storedCtx.getImageData(0, 0, w, h).data
        const img2 = currentCtx.getImageData(0, 0, w, h).data

        const debugging = this._debugDiv !== null
        let diffCanvas: HTMLCanvasElement | null = null
        let diffData: ImageData | null = null
        if (debugging) {
            diffCanvas = document.createElement('canvas')
            diffCanvas.width = w
            diffCanvas.height = h
            diffData = diffCanvas.getContext('2d')!.createImageData(w, h)
        }

        let changedPixels = 0
        let checkedPixels = 0
        for (let i = 0; i < img1.length; i += byteStep) {
            checkedPixels++
            const rDiff = Math.abs(img1[i] - img2[i])
            const gDiff = Math.abs(img1[i + 1] - img2[i + 1])
            const bDiff = Math.abs(img1[i + 2] - img2[i + 2])

            if ((rDiff + gDiff + bDiff) / 3 > this._pixelThreshold) {
                changedPixels++
                if (diffData) {
                    diffData.data[i] = 255
                    diffData.data[i + 1] = 0
                    diffData.data[i + 2] = 0
                    diffData.data[i + 3] = 255
                }
            } else if (diffData) {
                diffData.data[i] = 0
                diffData.data[i + 1] = 0
                diffData.data[i + 2] = 0
                diffData.data[i + 3] = 255
            }
        }
        if (diffCanvas && diffData) {
            diffCanvas.getContext('2d')!.putImageData(diffData, 0, 0)
        }

        const moved = changedPixels > this._threshold * checkedPixels
        return { moved, diffCanvas }
    }

    private imageChanged(current: HTMLCanvasElement): void {
        const fileName = `webcam_${crypto.randomUUID()}.jpg`
        const url = `${this._baseUrl}/cache/upload/${encodeURIComponent(fileName)}`

        current.toBlob(async (blob) => {
            if (!blob) return
            try {
                const buffer = await blob.arrayBuffer()
                const res = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-binary-stream' },
                    body: buffer,
                })
                if (!res.ok) throw new Error(await res.text())
                const msg = new Message('ImageEvent')
                msg.payload = { file_id: fileName }
                void this._client.push(msg)
            } catch (err) {
                console.error('webcam upload failed:', err)
            }
        }, 'image/jpeg', 0.8)

        const w = current.width
        const h = current.height
        if (this._storedCanvas === null) {
            this._storedCanvas = document.createElement('canvas')
            this._storedCanvas.width = w
            this._storedCanvas.height = h
        }
        const storedCtx = this._storedCanvas.getContext('2d')!
        storedCtx.drawImage(current, 0, 0)
    }

    private async _tick(): Promise<void> {
        const current = this._webcam.read()
        if (!current) return

        const { moved, diffCanvas } = this.detectMovement(current)

        if (moved) {
            this.imageChanged(current)
        }

        if (this._debugDiv !== null) {
            if (this._imgCurrent) this._imgCurrent.src = current.toDataURL('image/png')
            if (this._imgStored && this._storedCanvas) this._imgStored.src = this._storedCanvas.toDataURL('image/png')
            if (this._imgDiff && diffCanvas) this._imgDiff.src = diffCanvas.toDataURL('image/png')
        }
    }

    acceptDiv(div: HTMLDivElement): void {
        this._debugDiv = div

        const makeImg = (label: string): HTMLImageElement => {
            const wrapper = document.createElement('div')
            const title = document.createElement('span')
            title.textContent = label
            const img = document.createElement('img')
            img.style.maxWidth = '33%'
            wrapper.appendChild(title)
            wrapper.appendChild(img)
            div.appendChild(wrapper)
            return img
        }

        this._imgCurrent = makeImg('Current')
        this._imgStored = makeImg('Stored')
        this._imgDiff = makeImg('Diff')
    }

    release(): void {
        this._debugDiv = undefined
        this._imgCurrent = undefined
        this._imgStored = undefined
        this._imgDiff = undefined
    }
}
