import { SoundBuffer } from '../core/soundBuffer.js'
import { Dispatcher } from '../../core/dispatcher.js'
import { MicData } from '../input/micData.js'
import type { IWakeWordDetector } from './iWakeWordDetector.js'
import type { ILoadingScreenComponent } from '../../loadingScreen/index.js'

export class SilenceControllingWakeWordDetector implements IWakeWordDetector, ILoadingScreenComponent {
    get name(): string { return (this.detector as unknown as ILoadingScreenComponent).name }
    initialize(): Promise<void> { return (this.detector as unknown as ILoadingScreenComponent).initialize() }
    private buffer: SoundBuffer
    private silenceLevel: number
    private isActive = false
    private activationTimestamp: number | null = null
    private deactivationWindowMs: number
    private detector: IWakeWordDetector

    constructor({
        detector,
        dispatcher,
        silenceLevel = 0.1,
        bufferSeconds = 0.3,
        deactivationWindowSeconds = 0.5,
    }: {
        detector: IWakeWordDetector
        dispatcher: Dispatcher
        silenceLevel?: number
        bufferSeconds?: number
        deactivationWindowSeconds?: number
    }) {
        this.detector = detector
        this.silenceLevel = silenceLevel
        this.deactivationWindowMs = deactivationWindowSeconds * 1000
        this.buffer = new SoundBuffer({ maxTimeSeconds: bufferSeconds })
        dispatcher.subscribe('SetSilenceLevelCommand', async (msg) => {
            this.silenceLevel = msg.payload.level
        })
    }

    detect(micData: MicData): boolean {
        this.buffer.add(micData)
        const isSound = this.buffer.isFull && this.buffer.getLevel() >= this.silenceLevel

        if (isSound) {
            if (!this.isActive) {
                this.isActive = true
                this.activationTimestamp = micData.micTimestamp
                let result = false
                for (const frame of this.buffer.frames) {
                    if (this.detector.detect(frame)) result = true
                }
                return result
            }
            this.activationTimestamp = micData.micTimestamp
            return this.detector.detect(micData)
        }

        if (this.isActive) {
            const result = this.detector.detect(micData)
            if (this.activationTimestamp !== null &&
                micData.micTimestamp - this.activationTimestamp > this.deactivationWindowMs) {
                this.isActive = false
                this.activationTimestamp = null
                this.buffer.clear()
            }
            return result
        }

        return false
    }
}
