import { Dispatcher } from '../../core/dispatcher.js'
import { Message, Envelop } from '../../core/message.js'
import { MicData } from '../input/micData.js'
import { SilenceDetector } from './silenceDetector.js'
import { WakeWordDetector } from './wakeWordDetector.js'
import { StatefulRecorder, RecorderState } from './statefulRecorder.js'
import { SystemSoundSlot } from './systemSoundSlot.js'

enum StandbyPhase {
    WaitingForWakeWord,
    WaitingForSilence,
    WaitingForConfirmation,
}

export class Automaton {
    private standbyPhase = StandbyPhase.WaitingForWakeWord
    private openSlot: SystemSoundSlot
    private openedAt: number | null = null
    private lastOpeningWakeWordAt: number | null = null
    private openMicRequested = false
    private silenceDetector: SilenceDetector
    private wakeWordDetector: WakeWordDetector
    private statefulRecorder: StatefulRecorder
    private dispatcher: Dispatcher
    private maxSilenceInOpenTillError: number
    private maxNonSilenceAfterWakeWordTillReset: number

    constructor({
        silenceDetector,
        wakeWordDetector,
        statefulRecorder,
        dispatcher,
        maxSilenceInOpenTillError = 5,
        maxNonSilenceAfterWakeWordTillReset = 1,
    }: {
        silenceDetector: SilenceDetector,
        wakeWordDetector: WakeWordDetector,
        statefulRecorder: StatefulRecorder,
        dispatcher: Dispatcher,
        maxSilenceInOpenTillError?: number,
        maxNonSilenceAfterWakeWordTillReset?: number,
    }) {
        this.silenceDetector = silenceDetector
        this.wakeWordDetector = wakeWordDetector
        this.statefulRecorder = statefulRecorder
        this.dispatcher = dispatcher
        this.maxSilenceInOpenTillError = maxSilenceInOpenTillError
        this.maxNonSilenceAfterWakeWordTillReset = maxNonSilenceAfterWakeWordTillReset
        this.openSlot = new SystemSoundSlot({ soundName: 'open', dispatcher })
        dispatcher.subscribe('OpenMicCommand', async () => {
            this.openMicRequested = true
        })
    }

    async process(micData: MicData): Promise<void> {
        const isSilence = this.silenceDetector.isSilence(micData)
        const wakeWord = this.wakeWordDetector.detectWakeWord(micData)
        const nextState = this._getNextState(isSilence, wakeWord)
        if (nextState !== null) {
            this.statefulRecorder.setState(nextState)
        }
        await this.statefulRecorder.process(micData)
    }

    private _getNextState(isSilence: boolean, wakeWord: boolean): RecorderState | null {
        switch (this.statefulRecorder.state) {
            case RecorderState.Standby:
                return this._getNextStateStandBy(isSilence, wakeWord)
            case RecorderState.Open:
                if (!isSilence) return RecorderState.Record
                if (this.openedAt !== null &&
                    Date.now() - this.openedAt > this.maxSilenceInOpenTillError * 1000) {
                    this.dispatcher.push(new Message('SystemSoundCommand', new Envelop(), { sound_name: 'error' }))
                    this.standbyPhase = StandbyPhase.WaitingForWakeWord
                    return RecorderState.Standby
                }
                return null
            case RecorderState.Record:
                if (isSilence) {
                    this.dispatcher.push(new Message('SystemSoundCommand', new Envelop(), { sound_name: 'close' }))
                    return RecorderState.Commit
                }
                return null
            case RecorderState.Commit:
            case RecorderState.Cancel:
                return null
        }
    }

    private _getNextStateStandBy(isSilence: boolean, wakeWord: boolean): RecorderState | null {
        switch (this.standbyPhase) {
            case StandbyPhase.WaitingForWakeWord:
                if (wakeWord || this.openMicRequested) {
                    this.openMicRequested = false
                    this.lastOpeningWakeWordAt = Date.now()
                    this.standbyPhase = StandbyPhase.WaitingForSilence
                }
                return null
            case StandbyPhase.WaitingForSilence:
                if (this.lastOpeningWakeWordAt !== null &&
                    Date.now() - this.lastOpeningWakeWordAt > this.maxNonSilenceAfterWakeWordTillReset * 1000) {
                    this.lastOpeningWakeWordAt = null
                    this.standbyPhase = StandbyPhase.WaitingForWakeWord
                    return null
                }
                if (isSilence) {
                    this.lastOpeningWakeWordAt = null
                    this.openSlot.send()
                    this.standbyPhase = StandbyPhase.WaitingForConfirmation
                }
                return null
            case StandbyPhase.WaitingForConfirmation:
                if (this.openSlot.confirmed) {
                    this.openSlot.reset()
                    this.standbyPhase = StandbyPhase.WaitingForWakeWord
                    this.openedAt = Date.now()
                    return RecorderState.Open
                }
                return null
        }
    }
}
