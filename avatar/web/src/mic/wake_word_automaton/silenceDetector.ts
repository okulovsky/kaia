import { SoundBuffer } from '../core/soundBuffer.js'
import { Message, Envelop } from '../../core/message.js'
import { Dispatcher } from '../../core/dispatcher.js'
import { MicData } from '../input/micData.js'

export enum VoicePresence {
    Sound     = 'Sound',
    Silence   = 'Silence',
    Undefined = 'Undefined',
}

export class SilenceDetector {
    private timeBetweenReportsMs: number
    private decisionBuffer: SoundBuffer
    private reportingBuffer: SoundBuffer
    private decisionLevel: number | null = null
    private beginMicTimestamp: number | null = null
    private levels: number[]
    private silenceLevel: number
    private dispatcher: Dispatcher

    constructor({
        timeBetweenReportsInSeconds = 1,
        decisionWindowSeconds = 1.0,
        reportingWindowSeconds = 0.1,
        silenceLevel = 0.1,
        dispatcher,
    }: {
        timeBetweenReportsInSeconds?: number,
        decisionWindowSeconds?: number,
        reportingWindowSeconds?: number,
        silenceLevel?: number,
        dispatcher: Dispatcher,
    }) {
        this.dispatcher = dispatcher
        this.timeBetweenReportsMs = timeBetweenReportsInSeconds * 1000
        this.decisionBuffer = new SoundBuffer({ maxTimeSeconds: decisionWindowSeconds })
        this.reportingBuffer = new SoundBuffer({ maxTimeSeconds: reportingWindowSeconds })
        this.levels = []
        this.silenceLevel = silenceLevel
        dispatcher.subscribe('SetSilenceLevelCommand', async (msg) => {
            this.silenceLevel = msg.payload.level
        })
    }

    detect(micData: MicData): VoicePresence {
        if (this.beginMicTimestamp === null) this.beginMicTimestamp = micData.micTimestamp

        this.decisionBuffer.add(micData)
        if (this.decisionBuffer.isFull) {
            this.decisionLevel = this._computeLevelOf(this.decisionBuffer)
        }

        this.reportingBuffer.add(micData)
        if (this.reportingBuffer.isFull) {
            this.levels.push(this._computeLevelOf(this.reportingBuffer))
            this.reportingBuffer.clear()
        }

        if (micData.micTimestamp - this.beginMicTimestamp >= this.timeBetweenReportsMs) {
            this.dispatcher.push(new Message('SoundLevelReport', new Envelop(), {
                begin_timestamp: new Date(this.beginMicTimestamp).toISOString(),
                end_timestamp: new Date(micData.micTimestamp).toISOString(),
                levels: [...this.levels],
                silence_level: this.silenceLevel,
                decision_level: this.decisionLevel,
            }))
            this.beginMicTimestamp = micData.micTimestamp
            this.levels = []
        }

        if (this.decisionLevel === null) return VoicePresence.Undefined
        return this.decisionLevel < this.silenceLevel ? VoicePresence.Silence : VoicePresence.Sound
    }

    private _computeLevelOf(buffer: SoundBuffer): number {
        let sum = 0
        for (const s of buffer.buffer) {
            sum += Math.abs(s)
        }
        return sum / buffer.buffer.length
    }
}
