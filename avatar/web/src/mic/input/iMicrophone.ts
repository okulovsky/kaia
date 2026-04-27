import { MicData } from './micData.js'

export interface IMicrophone {
    start(): Promise<void>
    stop(): void
    read(): MicData | null
    isRunning(): boolean
}
