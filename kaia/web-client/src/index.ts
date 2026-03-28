import { UIControl, IUIControlConfig } from './uiControl'
import { AudioControl, IAudioControlConfig } from './audioControl.js'
import { AvatarClient } from '../../web-scripts'
import { AudioControlClient } from '../../web-scripts'
import { Dispatcher } from '../../web-scripts'
import { Message } from '../../web-scripts'
import { ChatCommandHandler } from '../../web-scripts'
import { ImageCommandHandler } from '../../web-scripts'
import { ButtonGridCommandHandler } from '../../web-scripts'
import { ServerStartedEventHandler } from '../../web-scripts'

interface IKaiaConfig {
    playSounds: boolean,
    sessionId: string

    wakeword: string
    voskModelUrl: string

    chatContainerId: string
    pictureContainerId: string,
    placeholderImagePath?: string,

    kaiaServerBaseUrl: string,
    audioServerBaseUrl: string,
    
    silenceThreshold?: number,
    silenceTimeDelta?: number,
    wakewordTimeDelta?: number,
    smoothingTimeConstant?: number,
    mediaRecorderChunkLength?: number,
    proxyUrl?: string
}

class KaiaApp {
    lastMessageIndex

    config: IKaiaConfig
    sessionId: string

    uiControl?: UIControl
    audioControl?: AudioControl

    avatarClient?: AvatarClient
    audioControlClient?: AudioControlClient
    dispatcher?: Dispatcher

    constructor (config: IKaiaConfig) {
        this.sessionId = config?.sessionId || Math.floor(Math.random() * 1000000).toString()
        this.lastMessageIndex = 0
        this.config = config
    }

    async initialize () {
        try {
            const uiControlConfig: IUIControlConfig = {
                chatContainerId: this.config.chatContainerId,
                pictureContainerId: this.config.pictureContainerId,
                placeholderImagePath: this.config.placeholderImagePath,
                proxyUrl: this.config.proxyUrl
            }

            const uiControl = new UIControl(uiControlConfig)

            const silenceThreshold = this.config.silenceThreshold || 15

            const audioControlConfig: Partial<IAudioControlConfig> = {
                wakeword: this.config.wakeword,
                voskModelUrl: this.config.voskModelUrl,
                silenceThreshold: silenceThreshold,
                silenceTimeDelta: this.config.silenceTimeDelta || 1500,
                wakewordTimeDelta: this.config.wakewordTimeDelta || 5000,
                smoothingTimeConstant: this.config.smoothingTimeConstant || 0.8,
                mediaRecorderChunkLength: this.config.mediaRecorderChunkLength || 100,

                playSounds: this.config.playSounds || true,
                onWakeword: () => uiControl.addChatMessage('Wakeword detected', { type: 'service' }),

                onStartRecording: () => {
                    uiControl.addChatMessage(`Recording just started`, { type: 'service' })
                },

                onRecordingChunk: async (index: number, audioChunks: Blob[]) => {
                    console.debug(`[kaia] Recording chunk reported: index=${index}, totalChunks=${audioChunks.length}`)
                    await audioControlClient.uploadAudioChunk(index, audioChunks)
                },

                onStopRecording: async () => {
                    console.debug('[kaia] Stopping recording')
                    const stopRecordingResponse = await audioControlClient.stopRecording()
                    console.debug('[kaia] Stop recording response:', stopRecordingResponse)  
                    uiControl.addChatMessage(`Recording saved to Kaia server, ${stopRecordingResponse.wav_filename}`, { type: 'service' })
                    if (stopRecordingResponse && stopRecordingResponse.wav_filename) { 
                        const sendAudioCommandResponse = await audioControlClient.sendCommandAudio(stopRecordingResponse.wav_filename)
                        console.debug('[kaia] Sent audio command', sendAudioCommandResponse)
                    }
                },

                onAudioPlayEnd: async (path: string) => {
                    console.debug(`[kaia] Audio play ended, ${path} sending confirmation signal`)
                    audioControlClient.sendConfirmationAudio(path)
                },

                onVolumeChange: async (volume: number) => {
                    uiControl._debugUpdateVolume(volume)
                },

                onStateChange: async (state: string) => {
                    uiControl._debugUpdateState(state)
                }
            }

            const audioControl = new AudioControl(audioControlConfig)
            await audioControl.initialize()

            this.audioControl = audioControl
            this.uiControl = uiControl

            uiControl._debugSetThreshold(silenceThreshold)

            const baseUrl = this.config.kaiaServerBaseUrl
            const avatarClient = new AvatarClient({ baseUrl, session: this.config.sessionId })
            this.avatarClient = avatarClient

            const audioControlBaseUrl = this.config.audioServerBaseUrl
            const audioControlClient = new AudioControlClient({ baseUrl, session: this.config.sessionId })

            try {
                const initMessage = new Message('InitializationEvent')
                await avatarClient.addMessage(initMessage)
                avatarClient.lastMessageId = (initMessage as any).envelop.id
            } catch (e) {
                console.error('[kaia] Failed to send InitializationEvent:', e)
            }

            const dispatcher = new Dispatcher(avatarClient, 1)
            this.dispatcher = dispatcher

            const chatDiv = document.getElementById('chatMessages') as HTMLElement
            const imageEl = document.getElementById('pictureDisplay') as HTMLImageElement
            let overlayDiv = document.getElementById('overlay') as HTMLDivElement | null
            if (!overlayDiv) {
                overlayDiv = document.createElement('div') as HTMLDivElement
                overlayDiv.id = 'overlay'
                document.body.appendChild(overlayDiv)
            }

            new ChatCommandHandler(dispatcher, chatDiv, this.config.kaiaServerBaseUrl)
            new ImageCommandHandler(dispatcher, imageEl)
            new ButtonGridCommandHandler(dispatcher, overlayDiv, avatarClient)
            new ServerStartedEventHandler(dispatcher)

            dispatcher.start()

            uiControl.addChatMessage(`Please say: "${this.config.wakeword}" and start talking.. Kaia client_id is ${this.config.sessionId}.`, { type: 'service' })
        } catch (error) {
            console.error('[kaia] Failed to initialize Kaia:', error)
        }
    }
}

let userConfig = {}

if (typeof window !== 'undefined') {
    const urlParams = new URLSearchParams(window.location.search)
    const configParam = urlParams.get('config')
    
    if (configParam) {
        try {
            userConfig = JSON.parse(decodeURIComponent(configParam))

            console.debug('[kaia] User config detected', userConfig)
        } catch (e) {
            console.error('[kaia] Failed to parse config from URL:', e)
        }
    }
}

const kaia = new KaiaApp({
    playSounds: true,

    sessionId: 'test',
    wakeword: 'computer',

    voskModelUrl: '/models/vosk-model-small-en-us-0.15.zip',

    chatContainerId: 'chatMessages',
    pictureContainerId: 'pictureDisplay',
    placeholderImagePath: 'placeholder.svg',

    kaiaServerBaseUrl: 'http://localhost:8890',
    audioServerBaseUrl: 'http://localhost:13000',
    
    silenceThreshold: 15,
    wakewordTimeDelta: 5000,

    ...userConfig
})

export default kaia