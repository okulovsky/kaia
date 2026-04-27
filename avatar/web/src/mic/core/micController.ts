import { IMicrophone } from '../input/iMicrophone.js'
import { MicData } from '../input/micData.js'

export type Processor<T = void> = (micData: MicData) => T

export class MicController {
    private timeoutId?: ReturnType<typeof setTimeout>
    private running = false

    constructor(
        private input: IMicrophone,
        private processor: Processor,
    ) {}

    async start(): Promise<void> {
        await this.input.start()
        this.running = true
        this._scheduleNext(10)
    }

    private _scheduleNext(delay: number): void {
        this.timeoutId = setTimeout(() => { void this._tick() }, delay)
    }

    private async _tick(): Promise<void> {
        if (!this.running) return
        let gotData = false
        while (this.running) {
            const micData = this.input.read()
            if (micData === null) break
            gotData = true
            await this.processor(micData)
        }
        if (this.running) {
            this._scheduleNext(gotData ? 10 : 100)
        }
    }

    stop(): void {
        this.running = false
        if (this.timeoutId !== undefined) {
            clearTimeout(this.timeoutId)
            this.timeoutId = undefined
        }
        this.input.stop()
    }
}
