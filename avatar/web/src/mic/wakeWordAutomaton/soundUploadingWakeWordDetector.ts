import { Dispatcher } from '../../core/dispatcher.js'
import { MicData } from '../input/micData.js'
import { Recorder } from './recorder.js'
import type { IWakeWordDetector } from './iWakeWordDetector.js'
import type { ILoadingScreenComponent } from '../../loadingScreen/index.js'

// Debugging aid: uploads whatever the wrapped detector hears as wakeword_<id>.wav.
// Wrapped inside a gate such as SilenceControllingWakeWordDetector, it is only fed frames
// while the gate is open, so every activation becomes its own file: the segment is committed
// once no frame has arrived for segmentTimeoutSeconds, and the next frame opens a new one.
// A segment in which the wrapped detector fired also gets an empty <name>.wav.activated
// companion, which is how a hit is told from a miss afterwards.
export class SoundUploadingWakeWordDetector implements IWakeWordDetector, ILoadingScreenComponent {
    get name(): string { return (this.detector as unknown as ILoadingScreenComponent).name }
    initialize(): Promise<void> { return (this.detector as unknown as ILoadingScreenComponent).initialize() }
    private detector: IWakeWordDetector
    private recorder: Recorder
    private baseUrl: string
    private segmentTimeoutMs: number
    private idleTimer: ReturnType<typeof setTimeout> | null = null
    private queue: Promise<void> = Promise.resolve()
    private markedThisSegment = false

    constructor({ detector, dispatcher, baseUrl = '', segmentTimeoutSeconds = 0.5 }: {
        detector: IWakeWordDetector,
        dispatcher: Dispatcher,
        baseUrl?: string,
        segmentTimeoutSeconds?: number,
    }) {
        this.detector = detector
        this.baseUrl = baseUrl.replace(/\/+$/, '')
        this.segmentTimeoutMs = segmentTimeoutSeconds * 1000
        this.recorder = new Recorder({
            startBufferLength: 0,
            dispatcher,
            baseUrl,
            filenamePrefix: 'wakeword_',
            // Silent: a SoundStreamingEndEvent would reach UploadedWavFixer and be replayed
            // into the pipeline as if the user had addressed Kaia.
            emitEvents: false,
        })
    }

    // Writes and commits share one Recorder, so they must not interleave: a write landing
    // mid-commit would append to the file being closed.
    private enqueue(operation: () => Promise<void>): void {
        this.queue = this.queue.then(operation).catch(console.error)
    }

    // An empty committed file: begin-writing creates it, commit just drops the sidecar.
    private async _writeMarker(filename: string): Promise<void> {
        for (const action of ['begin-writing', 'commit']) {
            const resp = await fetch(
                `${this.baseUrl}/streaming/${action}/${encodeURIComponent(filename)}`,
                { method: 'POST' }
            )
            if (!resp.ok) throw new Error(`[SoundUploading] ${action} failed: ${resp.status}`)
        }
    }

    detect(micData: MicData): boolean {
        this.enqueue(() => this.recorder.write(micData))

        if (this.idleTimer !== null) clearTimeout(this.idleTimer)
        this.idleTimer = setTimeout(() => {
            this.idleTimer = null
            this.enqueue(async () => {
                this.markedThisSegment = false
                await this.recorder.commit()
            })
        }, this.segmentTimeoutMs)

        const detected = this.detector.detect(micData)
        if (detected && !this.markedThisSegment) {
            this.markedThisSegment = true
            // Queued, so it runs after the write above has settled on a filename
            this.enqueue(async () => {
                const filename = this.recorder.currentFilename
                if (filename !== null) await this._writeMarker(`${filename}.activated`)
            })
        }
        return detected
    }
}
