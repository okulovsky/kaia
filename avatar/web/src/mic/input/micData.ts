export class MicData {
    readonly sampleRate: number
    readonly buffer: Float32Array
    readonly micTimestamp: number  // ms since epoch, advances by frameSize/sampleRate per frame
    readonly levelSum: number      // sum of Math.abs(buffer[i]) — precomputed for SoundBuffer

    constructor(sampleRate: number, buffer: Float32Array, micTimestamp: number) {
        this.sampleRate = sampleRate
        this.buffer = buffer
        this.micTimestamp = micTimestamp
        let sum = 0
        for (let i = 0; i < buffer.length; i++) sum += Math.abs(buffer[i])
        this.levelSum = sum
    }
}
