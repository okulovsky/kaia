import { MicData } from '../input/micData.js'

export interface IWakeWordDetector {
    detect(micData: MicData): boolean
}
