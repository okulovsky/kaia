import { IAudioInput } from '../input/iAudioInput.js'
import { MicData } from '../input/micData.js'

export type Processor<T = void> = (micData: MicData) => T

export class MicController {
    private intervalId?: ReturnType<typeof setInterval>

    constructor(
        private input: IAudioInput,
        private processor: Processor,
    ) {}

    async start(): Promise<void> {
        await this.input.start()
        this.intervalId = setInterval(() => this._tick(), 10)
    }

    private _tick(): void {
        this.processor(this.input.read())
    }

    stop(): void {
        if (this.intervalId !== undefined) {
            clearInterval(this.intervalId)
            this.intervalId = undefined
        }
        this.input.stop()
    }
}
