/**
 * AudioControl handles all audio playback and recording in Kaia
 *
 * It has three main components:
 *
 * 1. Wakeword detection
 * 2. Raw WAV recorder
 * 3. Volume control
 */

import { createModel } from 'vosk-browser'
import { RecognizerMessage } from 'vosk-browser/dist/interfaces'

export enum STATES {
    STANDBY = 'standby',
    OPEN = 'open',
    RECORDING = 'recording',
    PLAYING = 'playing',
}

export const ALLOWED_STATE_TRANSITIONS = {
    [STATES.STANDBY]: [STATES.OPEN, STATES.PLAYING],
    [STATES.OPEN]: [STATES.STANDBY, STATES.RECORDING, STATES.PLAYING],
    [STATES.RECORDING]: [STATES.STANDBY, STATES.PLAYING],
    [STATES.PLAYING]: [STATES.RECORDING, STATES.STANDBY, STATES.OPEN]
}

export interface IAudioControlConfig {
    wakeword: string
    voskModelUrl: string

    onWakeword: (recognizedWord: string) => void
    onStopRecording: (recordingId: string) => void
    onStartRecording: (recordingId: string) => void
    onRecordingChunk: (index: number, audioChunks: Blob[]) => void

    onVolumeChange?: (volume: number) => void
    onAudioPlayEnd?: (path: string) => void
    onStateChange?: (state: string) => void

    playSounds: boolean,

    // How much noise is considered silence?
    silenceThreshold: number

    // How much time to wait from silence start until ending recording
    silenceTimeDelta: number

    // How much time to wait from silence start until cancelling recording after wakeword has been detected
    wakewordTimeDelta: number

    // chunk length for mediarecorder
    recordingChunkLength: number

    // How often to collect chunks in milliseconds
    mediaRecorderChunkLength?: number

    sampleRate: number,
    volumeHistorySeconds: number,
    sampleInterval: number,
    fftSize: number,
    smoothingTimeConstant: number,
}

const DEFAULT_AUDIO_CONTROL_CONFIG: Partial<IAudioControlConfig> = {
    wakeword: 'computer',

    playSounds: false,

    recordingChunkLength: 1000, // Time between chunk sends in milliseconds

    silenceThreshold: 15,

    silenceTimeDelta: 1500,
    wakewordTimeDelta: 5000,

    mediaRecorderChunkLength: 100,
    sampleRate: 48000,
    volumeHistorySeconds: 0.5,
    sampleInterval: 60,
    fftSize: 256,
    smoothingTimeConstant: 0.8,
}

export class AudioControl {
    private config: IAudioControlConfig
    private state: STATES

    private audioStream?: MediaStream
    private audioContext?: AudioContext
    private analyser?: AnalyserNode

    private chunkIsBeingSent: boolean
    private currentRecordingId: string | null
    private audioChunks: Blob[]
    private lastChunkIndex: number
    private lastSendTime: number
    private audioWorkletNode?: AudioWorkletNode
    private volumeHistory: number[]
    private historyIndex: number

    private stopRecordingTimeoutId?: NodeJS.Timeout
    private startRecordingTimeoutId?: NodeJS.Timeout
    private volumeIsAboveThreshold = false

    private recognizerProcessor?: AudioWorkletNode

    constructor (userConfig: Partial<IAudioControlConfig>) {
        const config = { ...DEFAULT_AUDIO_CONTROL_CONFIG, ...userConfig } as IAudioControlConfig

        if (!config.recordingChunkLength || !config.mediaRecorderChunkLength) {
            throw new Error(`recordingChunkLength or mediaRecorderChunkLength are undefined`)
        }

        if (config.recordingChunkLength <= config.mediaRecorderChunkLength) {
            throw new Error(`RecordingChunkLength should be bigger then ${config.mediaRecorderChunkLength}`)
        }

        this.config = config

        this.state = STATES.STANDBY

        this.currentRecordingId = null
        this.audioChunks = []
        this.lastChunkIndex = 0
        this.lastSendTime = 0
        this.chunkIsBeingSent = false

        this.volumeHistory = new Array(this.config.volumeHistorySeconds * this.config.sampleInterval).fill(0)
        this.historyIndex = 0
    }

    async _changeState (newState: STATES): Promise<void> {

        const currentState = this.getCurrentState()

        if (this.config.onStateChange) {
            this.config.onStateChange(newState)
        }

        const allowedStateTransitionsForCurrentState = ALLOWED_STATE_TRANSITIONS[currentState]
        if (!allowedStateTransitionsForCurrentState.includes(newState)) {
            console.error(`[audioControl] Impossible to change state from ${this.state} to ${newState}`)
            return
        } else {
            console.debug(`[audioControl] changing state: from ${this.state} to ${newState}`)
        }

        if (currentState === STATES.OPEN) {
            if (newState === STATES.RECORDING) {
                await this._startRecording()
            }
        }

        if (currentState === STATES.RECORDING) {
            // This means that Kaia has interrupted user
            if (newState === STATES.PLAYING) {
                await this._cancelRecording()
            }

            if (newState === STATES.STANDBY) {
                await this._stopRecording()
            }
        }

        this.state = newState
    }

    _playStartSound () {
        if (!this.config.playSounds) { return }
        this._playSound('/sounds/beep_hi.wav')
    }

    _playErrorSound () {
        if (!this.config.playSounds) { return }
        this._playSound('/sounds/beep_error.wav')
    }

    _playStopSound () {
        if (!this.config.playSounds) { return }
        this._playSound('/sounds/beep_lo.wav')
    }

    _playSound (path: string, onPlaybackEnd: (() => void) | null = null) {
        const audio = new Audio(path)
        audio.play().catch(error => {
            console.warn('[audioControl] Failed to play start sound:', error)
        })

        audio.addEventListener("ended", () => {
            if (onPlaybackEnd) { onPlaybackEnd() }
        })
    }

    async initialize () {
        try {
            console.debug('[audioControl] Initializing audio control Microphone...')
            await this._setupMicrophone()

            console.debug('[audioControl] Initializing volume control...')
            await this._setupVolumeControl()

            console.debug('[audioControl] Initializing wakeword detection...')
            await this._setupVoiceRecognition()
        } catch (error) {
            console.error('[audioControl] Initialization failed:', error)
        }
    }

    async _onWakeword (word: string) {
        console.info('[audioControl] Wakeword detected')

        await this._changeState(STATES.OPEN)

        this.startRecordingTimeoutId = setTimeout(() => {
            if (this.getCurrentState() === STATES.OPEN) {
                this._changeState(STATES.STANDBY)
            }
        }, this.config.wakewordTimeDelta)

        this._playStartSound()

        if (this.config.onWakeword) {
            this.config.onWakeword(word)
        }
    }

    getCurrentState () {
        return this.state
    }

    async playAudio (path: string) {
        console.debug('[audioControl] playAudio signal detected')

        await this._changeState(STATES.PLAYING)

        this._playSound(path, () => {
            if (this.config.onAudioPlayEnd) {
                this._changeState(STATES.STANDBY)
                this.config.onAudioPlayEnd(path)
            }
        })
    }

    getVolume () {
        if (this.volumeHistory.length === 0) {
            return 0
        }

        return Math.round(
            this.volumeHistory.reduce((a, b) => a + b) / this.volumeHistory.length
        )
    }

    getVolumeThreshold () {
        return this.config.silenceThreshold
    }

    async _onVolumeAboveThreshold () {
        const currentState = this.getCurrentState()

        // User has started speaking again after pause
        if (currentState === STATES.RECORDING) {
            clearTimeout(this.stopRecordingTimeoutId )
        }

        // User started speaking after he said the wakeword
        if (currentState === STATES.OPEN) {
            clearTimeout(this.startRecordingTimeoutId )
            await this._changeState(STATES.RECORDING)
        }
    }

    async _onVolumeBelowThreshold () {
        const currentState = this.getCurrentState()

        if (currentState === STATES.RECORDING) {
            this.stopRecordingTimeoutId = setTimeout(() => {
                if (this.getCurrentState() === STATES.RECORDING) {
                    this._changeState(STATES.STANDBY)
                }
            }, this.config.silenceTimeDelta)
        }
    }

    async _sendPendingChunks () {
        console.debug(`[audioControl] Send pending chunks called. total chunks to send: ${this.audioChunks.length}`)

        const now = Date.now()

        if (this.audioChunks.length === 0) {
            return
        }

        const index = this.lastChunkIndex++
        const audioChunks = this.audioChunks

        try {
            await this.config.onRecordingChunk(index, audioChunks)

            this.audioChunks = []
            this.lastSendTime = now
        } catch (err) {
            console.error('[audioControl] failed to upload audio chunks', err)
        }
    }

    async _onRecordingChunkReady () {
        console.log('[audioControl] Recording chunk is ready')

        await this._sendPendingChunks()

        this.chunkIsBeingSent = false
    }

    async _setupMicrophone () {
        const audioStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                channelCount: 1
            }
        })

        // @ts-expect-error - In Apple garden you may not have access to AudioContext, but will have access to webkitAudioContext
        const audioContext = new (window.AudioContext || window.webkitAudioContext)()

        this.audioContext = audioContext
        this.audioStream = audioStream
        await this._setupAudioStreaming()
    }


    async _setupAudioStreaming () {
        if (!this.audioStream || !this.audioContext) {
            throw new Error('Audio stream or audio context are undefined')
        }

        const source = this.audioContext.createMediaStreamSource(this.audioStream)
        const processorUrl = new URL('/wav-recorder-processor.js', window.location.href).href

        await this.audioContext.audioWorklet.addModule(processorUrl)
        const audioWorkletNode = new AudioWorkletNode(this.audioContext, 'audio-recorder-processor')

        audioWorkletNode.port.onmessage = async (e) => {
            if (e.data.type === 'chunk') {
                const blob = new Blob([e.data.audioData], { type: 'audio/wav' })
                this.audioChunks.push(blob)

                if (!this.chunkIsBeingSent /** && this.getCurrentState() === STATES.RECORDING */) {
                    this.chunkIsBeingSent = true
                    try {
                        await this._onRecordingChunkReady()
                    } finally {
                        this.chunkIsBeingSent = false
                        this.lastSendTime = Date.now()
                    }
                }
            }
        }

        source.connect(audioWorkletNode)
        audioWorkletNode.connect(this.audioContext.destination)


        this.audioWorkletNode = audioWorkletNode
    }

    async _setupVolumeControl () {
        if (!this.audioContext || !this.audioStream) {
            throw new Error('Audio context or audio stream are not yet initialized')
        }

        const analyser = this.audioContext.createAnalyser()
        const microphone = this.audioContext.createMediaStreamSource(this.audioStream)
        microphone.connect(analyser)

        analyser.fftSize = this.config.fftSize
        analyser.smoothingTimeConstant = this.config.smoothingTimeConstant

        this.analyser = analyser

        const updateVolume = () => {
            const dataArray = new Uint8Array(analyser.frequencyBinCount)
            analyser.getByteFrequencyData(dataArray)

            const average = dataArray.reduce((a, b) => a + b) / dataArray.length
            this.volumeHistory[this.historyIndex] = Math.round(average)
            this.historyIndex = (this.historyIndex + 1) % this.volumeHistory.length

            const currentVolume = this.getVolume()
            const threshold = this.getVolumeThreshold()

            if (currentVolume >= threshold) {
                if (!this.volumeIsAboveThreshold) {
                    this.volumeIsAboveThreshold = true
                    this._onVolumeAboveThreshold()
                }
            } else {
                if (this.volumeIsAboveThreshold) {
                    this.volumeIsAboveThreshold = false
                    this._onVolumeBelowThreshold()
                }
            }

            if (this.config.onVolumeChange) {
                this.config.onVolumeChange(currentVolume)
            }

            requestAnimationFrame(updateVolume)
        }

        updateVolume()
    }

    async _setupVoiceRecognition () {
        if (!this.audioStream || !this.audioContext) {
            throw new Error('Audio stream or audio context are not yet initialized')
        }

        try {
            console.debug('[audioControl] Loading VOSK model from:', this.config.voskModelUrl)
            const channel = new MessageChannel()
            const model = await createModel(this.config.voskModelUrl)
            model.registerPort(channel.port1)

            const recognizer = new model.KaldiRecognizer(this.audioContext.sampleRate)
            recognizer.setWords(true)

            recognizer.on("result", (message: RecognizerMessage) => {

                // @ts-expect-error - RecognizerMessage structure varies by message type
                const word = message?.result?.text?.toLowerCase().trim() || ''

                console.debug('[audioControl] Recognition result:', message)

                this._processRecognizedWord(word)
            })

            const processorUrl = new URL('recognizer-processor.js', window.location.href).href
            await this.audioContext.audioWorklet.addModule(processorUrl)

            const recognizerProcessor = new AudioWorkletNode(this.audioContext, 'recognizer-processor', {
                channelCount: 1
            })
            this.recognizerProcessor = recognizerProcessor  // <- сохранили

            recognizerProcessor.port.postMessage(
                { action: 'init', recognizerId: recognizer.id },
                [channel.port2]
            )

            const source = this.audioContext.createMediaStreamSource(this.audioStream)
            source.connect(recognizerProcessor)
            recognizerProcessor.connect(this.audioContext.destination)
        } catch (error) {
            console.error('[audioControl] Voice recognition initialization error:', error)
            throw error
        }
    }

    _processRecognizedWord (word: string) {
        if (word === this.config.wakeword) {
            this._onWakeword(word)
        }
    }

    async _cancelRecording () {
        console.debug('[audioControl] Cancelling recording...')

        this.audioChunks = []
        this.lastChunkIndex = 0
        this.lastSendTime = 0
    }

    async _stopRecording () {
        if (!this.audioWorkletNode) {
            throw new Error('Audio worklet node is not properly initialized')
        }

        if (this.getCurrentState() !== STATES.RECORDING) {
            return
        }

        console.debug('[audioControl] Ending recording...')

        try {
            this.audioWorkletNode.port.postMessage({ command: 'stop' })

            await this._sendPendingChunks()

            if (this.config.onStopRecording && this.currentRecordingId) {
                await this.config.onStopRecording(this.currentRecordingId)
            }

            console.debug('[audioControl] Recording stopped successfully')
            this._playStopSound()
        } catch (error) {
            console.error('[audioControl] Error stopping recording:', error)
            this._playErrorSound()
        }
    }

    async _startRecording () {
        if (this.getCurrentState() !== STATES.OPEN) {
            return
        }

        if (!this.audioWorkletNode) {
            throw new Error('Audio worklet node is not properly initialized')
        }

        console.debug('[audioControl] Starting recording...')

        this.audioChunks = []
        this.currentRecordingId = Date.now().toString()
        this.audioWorkletNode.port.postMessage({ command: 'start' })

        if (this.config.onStartRecording && this.currentRecordingId) {
            await this.config.onStartRecording(this.currentRecordingId)
        }
    }
}