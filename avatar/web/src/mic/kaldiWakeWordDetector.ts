import { createModel } from 'vosk-browser'
import type { KaldiRecognizer, Model } from 'vosk-browser'
import { Message, Envelop, Dispatcher } from '../core/index.js'
import { MicData } from './input/index.js'
import type { IWakeWordDetector } from './wakeWordAutomaton/index.js'
import type { ILoadingScreenComponent } from '../../loadingScreen/index.js'


export class KaldiWakeWordDetector implements ILoadingScreenComponent, IWakeWordDetector {
    readonly name = 'KaldiWakeWordDetector'
    private sampleRateOfTheModel: number
    private words: string[]
    private modelUrl: string
    private recognizer?: KaldiRecognizer
    private recognizerPort?: MessagePort
    private recognizerId?: number
    private initialized = false
    private _detected = false
    private dispatcher: Dispatcher

    constructor({ sampleRateOfTheModel, words, modelUrl, dispatcher }: {
        sampleRateOfTheModel: number,
        words: string[],
        modelUrl: string,
        dispatcher: Dispatcher,
    }) {
        this.sampleRateOfTheModel = sampleRateOfTheModel
        this.words = words.map(w => w.toLowerCase())
        this.modelUrl = modelUrl
        this.dispatcher = dispatcher
    }

    isInitialized(): boolean {
        return this.initialized
    }

    async initialize(): Promise<void> {
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

    detect(micData: MicData): boolean {
        if (!this.initialized) return false

        // Vosk expects PCM amplitude range (~±32768), not normalized [-1, 1]
        const scaled = new Float32Array(micData.buffer.length)
        for (let i = 0; i < micData.buffer.length; i++) scaled[i] = micData.buffer[i] * 32768

        this.recognizerPort!.postMessage(
            { action: 'audioChunk', data: scaled, recognizerId: this.recognizerId, sampleRate: this.sampleRateOfTheModel },
            { transfer: [scaled.buffer] }
        )

        const detected = this._detected
        this._detected = false
        return detected
    }
}
