import { Dispatcher } from '../../core/dispatcher.js'
import { MicData } from '../input/micData.js'
import { SilenceDetector, VoicePresence } from './silenceDetector.js'
import { StatefulRecorder, RecorderState } from './statefulRecorder.js'

/**
 * A wake-word-free counterpart of the Automaton: the voice itself opens the mic.
 *
 * The recorder is kept in Open (so the pre-roll buffer always holds the last
 * second of sound), the first non-silent frame switches it to Record, and the
 * next silence commits the file. Nothing else is needed to talk to the backend:
 * the Recorder uploads while recording and posts SoundStreamingEndEvent on commit.
 *
 * Because there is no wake word to protect it, the mic would otherwise hear the
 * avatar's own voice and answer itself. So every SoundCommand mutes it, and it
 * only opens again once the playback has been confirmed.
 */
export class VoiceActivityAutomaton {
    private silenceDetector: SilenceDetector
    private statefulRecorder: StatefulRecorder
    private currentMicTime = 0
    private recordingSince: number | null = null
    private mutedSince: number | null = null
    private unmutingAt: number | null = null
    private soundsBeingPlayed = 0
    private maximalRecordDurationInSeconds: number
    private unmuteDelayInSeconds: number
    private maximalMuteDurationInSeconds: number

    /**
     * @param silenceDetector              decides whether a frame is voice or silence
     * @param statefulRecorder             the recorder this automaton drives
     * @param dispatcher                   dispatches incoming Messages
     * @param maximalRecordDurationInSeconds  commits a recording that never falls silent
     * @param unmuteDelayInSeconds         how long to keep the mic shut after a playback, for the echo to die out
     * @param maximalMuteDurationInSeconds unmutes anyway if a SoundCommand is never confirmed
     */
    constructor({
        silenceDetector,
        statefulRecorder,
        dispatcher,
        maximalRecordDurationInSeconds = 60,
        unmuteDelayInSeconds = 0.5,
        maximalMuteDurationInSeconds = 120,
    }: {
        silenceDetector: SilenceDetector,
        statefulRecorder: StatefulRecorder,
        dispatcher: Dispatcher,
        maximalRecordDurationInSeconds?: number,
        unmuteDelayInSeconds?: number,
        maximalMuteDurationInSeconds?: number,
    }) {
        this.silenceDetector = silenceDetector
        this.statefulRecorder = statefulRecorder
        this.maximalRecordDurationInSeconds = maximalRecordDurationInSeconds
        this.unmuteDelayInSeconds = unmuteDelayInSeconds
        this.maximalMuteDurationInSeconds = maximalMuteDurationInSeconds

        dispatcher.subscribe('SoundCommand', async () => {
            this.soundsBeingPlayed++
            this.unmutingAt = null
            if (this.mutedSince === null) this.mutedSince = this.currentMicTime
        })
        dispatcher.subscribe('SoundConfirmation', async () => {
            if (this.soundsBeingPlayed > 0) this.soundsBeingPlayed--
            if (this.soundsBeingPlayed === 0) {
                this.unmutingAt = this.currentMicTime + this.unmuteDelayInSeconds * 1000
            }
        })
    }

    get isMuted(): boolean {
        return this.mutedSince !== null
    }

    async process(micData: MicData): Promise<void> {
        this.currentMicTime = micData.micTimestamp
        const presence = this.silenceDetector.detect(micData)
        this._updateMuting()
        const nextState = this._getNextState(presence)
        if (nextState !== null) {
            if (nextState === RecorderState.Record && this.recordingSince === null) {
                this.recordingSince = this.currentMicTime
            }
            if (nextState !== RecorderState.Record) {
                this.recordingSince = null
            }
            this.statefulRecorder.setState(nextState)
        }
        await this.statefulRecorder.process(micData)
    }

    private _updateMuting(): void {
        if (this.mutedSince === null) return
        const expired = this.currentMicTime - this.mutedSince > this.maximalMuteDurationInSeconds * 1000
        if (expired) {
            this.soundsBeingPlayed = 0
            this.unmutingAt = null
            this.mutedSince = null
            return
        }
        if (this.unmutingAt !== null && this.currentMicTime >= this.unmutingAt) {
            this.unmutingAt = null
            this.mutedSince = null
        }
    }

    private _getNextState(presence: VoicePresence): RecorderState | null {
        switch (this.statefulRecorder.state) {
            case RecorderState.Standby:
                return this.isMuted ? null : RecorderState.Open
            case RecorderState.Open:
                if (this.isMuted) return RecorderState.Standby
                if (presence === VoicePresence.Sound) return RecorderState.Record
                return null
            case RecorderState.Record:
                if (this.isMuted) return RecorderState.Cancel
                if (presence === VoicePresence.Silence) return RecorderState.Commit
                if (this.recordingSince !== null &&
                    this.currentMicTime - this.recordingSince > this.maximalRecordDurationInSeconds * 1000) {
                    return RecorderState.Commit
                }
                return null
            case RecorderState.Commit:
            case RecorderState.Cancel:
                return null
        }
    }
}
