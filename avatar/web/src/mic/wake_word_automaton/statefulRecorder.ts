import { MicData } from '../input/micData.js'
import { Dispatcher } from '../../core/dispatcher.js'
import { Message, Envelop } from '../../core/message.js'
import { Recorder } from './recorder.js'

export enum RecorderState {
    Standby = 'Standby',
    Open    = 'Open',
    Record  = 'Record',
    Commit  = 'Commit',
    Cancel  = 'Cancel',
}

export class StatefulRecorder {
    private _state: RecorderState = RecorderState.Standby
    private recorder: Recorder
    private dispatcher: Dispatcher

    get state(): RecorderState {
        return this._state
    }

    constructor({
        recorder,
        dispatcher,
        subscribeToDirectStateChange = false,
    }: {
        recorder: Recorder,
        dispatcher: Dispatcher,
        subscribeToDirectStateChange?: boolean,
    }) {
        this.recorder = recorder
        this.dispatcher = dispatcher
        if (subscribeToDirectStateChange) {
            dispatcher.subscribe('StatefulRecorderStateCommand', async (msg) => {
                const name = msg.payload.state as string
                const next = RecorderState[name as keyof typeof RecorderState]
                if (next !== undefined) {
                    this.setState(next)
                } else {
                    console.error(`[StatefulRecorder] unknown state: ${name}`)
                }
            })
        }
    }

    setState(newState: RecorderState): void {
        if (newState === this._state) return
        this._state = newState
        this.dispatcher.push(new Message('StatefulRecorderStateEvent', new Envelop(), {
            state: newState,
        }))
    }

    async process(micData: MicData): Promise<void> {
        switch (this._state) {
            case RecorderState.Standby:
                break
            case RecorderState.Open:
                this.recorder.observe(micData)
                break
            case RecorderState.Record:
                await this.recorder.write(micData)
                break
            case RecorderState.Commit:
                this.setState(RecorderState.Standby)
                await this.recorder.commit()
                break
            case RecorderState.Cancel:
                this.setState(RecorderState.Standby)
                await this.recorder.cancel()
                break
        }
    }
}
