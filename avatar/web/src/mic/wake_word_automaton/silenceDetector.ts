import { SoundBuffer } from '../core/soundBuffer.js'
import { Message, Envelop } from '../../core/message.js'
import { Dispatcher } from '../../core/dispatcher.js'
import { MicData } from '../input/micData.js'

export class SilenceDetector {
    private timeBetweenReportsMs: number
    private buffer: SoundBuffer
    private beginTimestamp: number
    private levels: number[]
    private silenceLevel: number
    private dispatcher: Dispatcher

    constructor({
        timeBetweenReportsInSeconds = 1,
        discretizationInSeconds = 0.05,
        silenceLevel = 0.1,
        dispatcher,
    }: {
        timeBetweenReportsInSeconds?: number,
        discretizationInSeconds?: number,
        silenceLevel?: number,
        dispatcher: Dispatcher,
    }) {
        this.dispatcher = dispatcher
        this.timeBetweenReportsMs = timeBetweenReportsInSeconds * 1000
        this.buffer = new SoundBuffer({ maxTimeSeconds: discretizationInSeconds })
        this.beginTimestamp = Date.now()
        this.levels = []
        this.silenceLevel = silenceLevel
        dispatcher.subscribe('SetSilenceLevelCommand', async (msg) => {
            this.silenceLevel = msg.payload.level
        })
    }

    isSilence(micData: MicData): boolean {
        const now = Date.now()

        this.buffer.add(micData)
        if (this.buffer.isFull) {
            this.levels.push(this._computeLevel())
            this.buffer.clear()
        }

        if (now - this.beginTimestamp >= this.timeBetweenReportsMs) {
            this.dispatcher.push(new Message('SoundLevelReport', new Envelop(), {
                begin_timestamp: new Date(this.beginTimestamp).toISOString(),
                end_timestamp: new Date(now).toISOString(),
                levels: [...this.levels],
                silence_level: this.silenceLevel,
            }))
            this.beginTimestamp = now
            this.levels = []
        }

        const level = this.levels.length > 0
            ? this.levels[this.levels.length - 1]
            : 0
        return level < this.silenceLevel
    }

    private _computeLevel(): number {
        let sum = 0
        for (const s of this.buffer.buffer) {
            sum += Math.abs(s)
        }
        return sum / this.buffer.buffer.length
    }
}
