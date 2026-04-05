export interface MicData {
    sampleRate: number
    buffer: Float32Array
    micTimestamp: number  // ms since epoch, advances by frameSize/sampleRate per frame
}
