import { Message, Envelop, Dispatcher } from '../core/index.js'
import type { MicData } from './input/index.js'
import type { IWakeWordDetector } from './wakeWordAutomaton/index.js'
import type { ILoadingScreenComponent } from '../../loadingScreen/index.js'

// Hotword binary data shipped with the bumblebee-hotword npm package.
// Available names: alexa, bumblebee, computer, grasshopper, hey_edison,
// hey_google, hey_siri, jarvis, ok_google, porcupine, terminator.
// @ts-ignore — CJS module, no type declarations
import computer from 'bumblebee-hotword/hotwords/computer'
// @ts-ignore
import jarvis from 'bumblebee-hotword/hotwords/jarvis'
// @ts-ignore
import bumblebee from 'bumblebee-hotword/hotwords/bumblebee'
// @ts-ignore
import alexa from 'bumblebee-hotword/hotwords/alexa'
// @ts-ignore
import grasshopper from 'bumblebee-hotword/hotwords/grasshopper'
// @ts-ignore
import hey_edison from 'bumblebee-hotword/hotwords/hey_edison'
// @ts-ignore
import hey_google from 'bumblebee-hotword/hotwords/hey_google'
// @ts-ignore
import hey_siri from 'bumblebee-hotword/hotwords/hey_siri'
// @ts-ignore
import ok_google from 'bumblebee-hotword/hotwords/ok_google'
// @ts-ignore
import porcupine from 'bumblebee-hotword/hotwords/porcupine'
// @ts-ignore
import terminator from 'bumblebee-hotword/hotwords/terminator'

const HOTWORD_DATA: Record<string, Uint8Array> = {
    alexa, bumblebee, computer, grasshopper,
    hey_edison, hey_google, hey_siri, jarvis,
    ok_google, porcupine, terminator,
}

export class BumblebeeWakeWordDetector implements ILoadingScreenComponent, IWakeWordDetector {
    readonly name = 'BumblebeeWakeWordDetector'

    private readonly words: string[]
    private readonly sensitivity: number
    private readonly dispatcher: Dispatcher
    private readonly workersPath: string

    private porcupineWorker?: Worker
    private initialized = false
    private _detected = false

    constructor({ words, sensitivity = 0.5, dispatcher, workersPath = '/frontend/bumblebee-workers' }: {
        words: string[],
        sensitivity?: number,
        dispatcher: Dispatcher,
        workersPath?: string,
    }) {
        for (const word of words) {
            if (!(word in HOTWORD_DATA)) {
                throw new Error(
                    `Unknown bumblebee hotword: "${word}". ` +
                    `Available: ${Object.keys(HOTWORD_DATA).join(', ')}`
                )
            }
        }
        this.words = words
        this.sensitivity = sensitivity
        this.dispatcher = dispatcher
        this.workersPath = workersPath
    }

    isInitialized(): boolean {
        return this.initialized
    }

    async initialize(): Promise<void> {
        this.porcupineWorker = new Worker(`${this.workersPath}/porcupine_worker.js`)

        this.porcupineWorker.onmessage = (e: MessageEvent) => {
            const keyword: string | null = e.data.keyword
            if (keyword !== null) {
                this._detected = true
                this.dispatcher.push(new Message('WakeWordEvent', new Envelop(), { word: keyword }))
            }
        }

        const keywordIDs: Record<string, Uint8Array> = {}
        for (const word of this.words) {
            keywordIDs[word] = HOTWORD_DATA[word]
        }
        const sensitivities = new Float32Array(this.words.map(() => this.sensitivity))

        this.porcupineWorker.postMessage({ command: 'init', keywordIDs, sensitivities })
        this.initialized = true
    }

    detect(micData: MicData): boolean {
        if (!this.initialized) return false

        const outputFrame = new Int16Array(micData.buffer.length)
        for (let i = 0; i < micData.buffer.length; i++) {
            outputFrame[i] = micData.buffer[i] * 32767
        }
        this.porcupineWorker!.postMessage({
            command: 'process',
            inputFrame: outputFrame,
            inputFrameFloat: micData.buffer,
        })

        const detected = this._detected
        this._detected = false
        return detected
    }
}
