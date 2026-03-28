/* global AudioWorkletProcessor, registerProcessor, sampleRate */

class WavEncoder {
  constructor (sampleRate) {
    this.sampleRate = sampleRate
    this.numberOfChannels = 1
    this.bytesPerSample = 2
    this.audioData = []
  }

  addAudioData (data) {
    this.audioData.push(...data)
  }

  getWavBuffer () {
    const buffer = new ArrayBuffer(44 + this.audioData.length * 2)
    const view = new DataView(buffer)

    // Write WAV header
    this.writeString(view, 0, 'RIFF')
    view.setUint32(4, 36 + this.audioData.length * 2, true)
    this.writeString(view, 8, 'WAVE')
    this.writeString(view, 12, 'fmt ')
    view.setUint32(16, 16, true)
    view.setUint16(20, 1, true)
    view.setUint16(22, this.numberOfChannels, true)
    view.setUint32(24, this.sampleRate, true)
    view.setUint32(28, this.sampleRate * this.numberOfChannels * this.bytesPerSample, true)
    view.setUint16(32, this.numberOfChannels * this.bytesPerSample, true)
    view.setUint16(34, 16, true)
    this.writeString(view, 36, 'data')
    view.setUint32(40, this.audioData.length * 2, true)

    // Write audio data
    this.floatTo16BitPCM(view, 44, this.audioData)
    
    // Reset buffer after getting WAV
    this.audioData = []
    
    return buffer
  }

  writeString (view, offset, string) {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i))
    }
  }

  floatTo16BitPCM (view, offset, input) {
    for (let i = 0; i < input.length; i++, offset += 2) {
      const s = Math.max(-1, Math.min(1, input[i]))
      view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true)
    }
  }
}

class AudioRecorderProcessor extends AudioWorkletProcessor {
  constructor () {
    super()
    this.isRecording = false
    this.encoder = new WavEncoder(sampleRate)
    this.processedFrames = 0
    this.chunkInterval = 1000 // 1 second chunks

    this.port.onmessage = (event) => {
      if (event.data.command === 'start') {
        this.isRecording = true
        this.processedFrames = 0
      } else if (event.data.command === 'stop') {
        this.isRecording = false
        this.sendWavChunk()
      }
    }
  }

  sendWavChunk () {
    const wavBuffer = this.encoder.getWavBuffer()
    this.port.postMessage({
      type: 'chunk',
      audioData: wavBuffer
    }, [wavBuffer])
  }

  process (inputs) {
    if (!this.isRecording) {
      return true
    }

    const input = inputs[0]
    if (input.length > 0) {
      const audioData = input[0]
      this.encoder.addAudioData(audioData)
      
      this.processedFrames += 128 // Standard AudioWorklet buffer size
      const currentTimeMs = (this.processedFrames / sampleRate) * 1000
      
      if (currentTimeMs >= this.chunkInterval) {
        this.sendWavChunk()
        this.processedFrames = 0
      }
    }

    return true
  }
}

registerProcessor('audio-recorder-processor', AudioRecorderProcessor) 