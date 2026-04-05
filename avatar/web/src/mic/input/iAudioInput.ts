import { MicData } from './micData.js'

export interface IAudioInput {
    start(): Promise<void>
    stop(): void
    read(): MicData | null
    isRunning(): boolean
}
