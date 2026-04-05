import { Dispatcher } from '../../core/dispatcher.js'
import { Message, Envelop } from '../../core/message.js'
import { MicData } from '../input/micData.js'
import { SilenceDetector, VoicePresence } from './silenceDetector.js'
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
    private currentMicTime = 0
    private silenceDetector: SilenceDetector
    private wakeWordDetector: WakeWordDetector | null
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
        wakeWordDetector: WakeWordDetector | null,
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
        this.currentMicTime = micData.micTimestamp
        const presence = this.silenceDetector.detect(micData)
        const wakeWord = this.wakeWordDetector?.detectWakeWord(micData) ?? false
        const nextState = this._getNextState(presence, wakeWord)
        if (nextState !== null) {
            this.statefulRecorder.setState(nextState)
        }
        await this.statefulRecorder.process(micData)
    }

    private _getNextState(presence: VoicePresence, wakeWord: boolean): RecorderState | null {
        switch (this.statefulRecorder.state) {
            case RecorderState.Standby:
                return this._getNextStateStandBy(presence, wakeWord)
            case RecorderState.Open:
                if (presence === VoicePresence.Sound) return RecorderState.Record
                if (this.openedAt !== null &&
                    this.currentMicTime - this.openedAt > this.maxSilenceInOpenTillError * 1000) {
                    this.dispatcher.push(new Message('SystemSoundCommand', new Envelop(), { sound_name: 'error' }))
                    this.standbyPhase = StandbyPhase.WaitingForWakeWord
                    return RecorderState.Standby
                }
                return null
            case RecorderState.Record:
                if (presence === VoicePresence.Silence) {
                    this.dispatcher.push(new Message('SystemSoundCommand', new Envelop(), { sound_name: 'close' }))
                    return RecorderState.Commit
                }
                return null
            case RecorderState.Commit:
            case RecorderState.Cancel:
                return null
        }
    }

    private _getNextStateStandBy(presence: VoicePresence, wakeWord: boolean): RecorderState | null {
        switch (this.standbyPhase) {
            case StandbyPhase.WaitingForWakeWord:
                if (wakeWord || this.openMicRequested) {
                    this.openMicRequested = false
                    this.lastOpeningWakeWordAt = this.currentMicTime
                    this.standbyPhase = StandbyPhase.WaitingForSilence
                }
                return null
            case StandbyPhase.WaitingForSilence:
                if (this.lastOpeningWakeWordAt !== null &&
                    this.currentMicTime - this.lastOpeningWakeWordAt > this.maxNonSilenceAfterWakeWordTillReset * 1000) {
                    this.lastOpeningWakeWordAt = null
                    this.standbyPhase = StandbyPhase.WaitingForWakeWord
                    return null
                }
                if (presence === VoicePresence.Silence) {
                    this.lastOpeningWakeWordAt = null
                    this.openSlot.send()
                    this.standbyPhase = StandbyPhase.WaitingForConfirmation
                }
                return null
            case StandbyPhase.WaitingForConfirmation:
                if (this.openSlot.confirmed) {
                    this.openSlot.reset()
                    this.standbyPhase = StandbyPhase.WaitingForWakeWord
                    this.openedAt = this.currentMicTime
                    return RecorderState.Open
                }
                return null
        }
    }
}
