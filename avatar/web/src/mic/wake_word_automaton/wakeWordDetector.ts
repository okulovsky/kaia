import { createModel } from 'vosk-browser'
import type { KaldiRecognizer, Model } from 'vosk-browser'
import { Message, Envelop } from '../../core/message.js'
import { Dispatcher } from '../../core/dispatcher.js'
import { MicData } from '../input/micData.js'
import { Recorder } from './recorder.js'

export class WakeWordDetector {
    private sampleRateOfTheModel: number
    private words: string[]
    private modelUrl: string
    private recognizer?: KaldiRecognizer
    private recognizerPort?: MessagePort
    private recognizerId?: number
    private initializing = false
    private initialized = false
    private _detected = false
    private dispatcher: Dispatcher
    private debugRecorder: Recorder | null = null

    constructor({ sampleRateOfTheModel, words, modelUrl, dispatcher, uploadDebugSound = false, baseUrl = '' }: {
        sampleRateOfTheModel: number,
        words: string[],
        modelUrl: string,
        dispatcher: Dispatcher,
        uploadDebugSound?: boolean,
        baseUrl?: string,
    }) {
        this.sampleRateOfTheModel = sampleRateOfTheModel
        this.words = words.map(w => w.toLowerCase())
        this.modelUrl = modelUrl
        this.dispatcher = dispatcher
        if (uploadDebugSound) {
            this.debugRecorder = new Recorder({ startBufferLength: 0, dispatcher, baseUrl })
        }
    }

    isInitialized(): boolean {
        return this.initialized
    }

    private async _initialize(): Promise<void> {
        const channel = new MessageChannel()
        const model: Model = await createModel(this.modelUrl)
        model.registerPort(channel.port1)

        this.recognizer = new model.KaldiRecognizer(this.sampleRateOfTheModel)
        this.recognizer.setWords(true)
        this.recognizerPort = channel.port2
        this.recognizerId = this.recognizer.id

        this.recognizer.on('result', (message: any) => {
            const text: string = message?.result?.text?.toLowerCase().trim() ?? ''
            if (text && this.words.includes(text)) {
                this._detected = true
                this.dispatcher.push(new Message('WakeWordEvent', new Envelop(), { word: text }))
            }
        })

        this.initialized = true
    }

    private _resample(input: Float32Array, fromRate: number): Float32Array {
        if (fromRate === this.sampleRateOfTheModel) return input.slice()
        const ratio = fromRate / this.sampleRateOfTheModel
        const outputLength = Math.round(input.length / ratio)
        const output = new Float32Array(outputLength)
        for (let i = 0; i < outputLength; i++) {
            const srcIdx = i * ratio
            const idx = Math.floor(srcIdx)
            const frac = srcIdx - idx
            const a = input[idx] ?? 0
            const b = input[idx + 1] ?? a
            output[i] = a + frac * (b - a)
        }
        return output
    }

    detectWakeWord(micData: MicData): boolean {
        if (!this.initialized) {
            if (!this.initializing) {
                this.initializing = true
                this._initialize().catch(console.error)
            }
            return false
        }

        const float32 = this._resample(micData.buffer, micData.sampleRate)

        if (this.debugRecorder) {
            this.debugRecorder.write({ sampleRate: this.sampleRateOfTheModel, buffer: float32.slice() }).catch(console.error)
        }

        // Vosk expects PCM amplitude range (~±32768), not normalized [-1, 1]
        const scaled = new Float32Array(float32.length)
        for (let i = 0; i < float32.length; i++) scaled[i] = float32[i] * 32768

        this.recognizerPort!.postMessage(
            { action: 'audioChunk', data: scaled, recognizerId: this.recognizerId, sampleRate: this.sampleRateOfTheModel },
            { transfer: [scaled.buffer] }
        )

        const detected = this._detected
        this._detected = false
        return detected
    }
}
