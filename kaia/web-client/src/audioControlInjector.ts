import { AudioControl } from './audioControl'

/**
 * AudioControlInjector allows injecting an external audio file into AudioControl's processing pipeline.
 *
 * Usage:
 *   const injector = new AudioControlInjector(audioControl)
 *   await audioControl.initialize()
 *   await injector.inject_audio('/path/to/test.wav')
 */
export class AudioControlInjector {
  private audioControl: AudioControl

  constructor (audioControl: AudioControl) {
    this.audioControl = audioControl
  }

  /**
   * Starts persistent silence by pumping a silent buffer into AudioControl's worklet, analyzer, and recognizer.
   */
  private startPersistentSilence (): void {
    const ac: any = this.audioControl
    const ctx: AudioContext = ac.audioContext
    const workletNode: AudioWorkletNode = ac.audioWorkletNode
    const analyser: AnalyserNode = ac.analyser
    const recognizerProcessor: AudioWorkletNode = ac.recognizerProcessor

    if (!ctx || !workletNode || !analyser || !recognizerProcessor) {
      console.error('[AudioControlInjector] Cannot start silence: AudioControl not fully initialized')
      return
    }

    // Stop any existing silence source
    if (ac.persistentSilenceSource) {
      try {
        ac.persistentSilenceSource.stop()
        ac.persistentSilenceSource.disconnect()
      } catch {}
      ac.persistentSilenceSource = undefined
    }

    const sr = ctx.sampleRate
    const buf = ctx.createBuffer(1, Math.ceil(0.1 * sr), sr)
    const src = ctx.createBufferSource()
    src.buffer = buf
    src.loop = true

    // Pipe silence into the same processing nodes
    src.connect(workletNode)
    src.connect(analyser)
    src.connect(recognizerProcessor)
    src.start()

    ac.persistentSilenceSource = src
    console.debug('[AudioControlInjector] Persistent silence started')
  }

  /**
   * Fetches an audio file, decodes it, plays it through AudioControl's worklet, analyzer, and recognizer,
   * then switches to persistent silence.
   */
  injectAudio = async (url: string): Promise<void> => {
    const ac: any = this.audioControl
    const ctx: AudioContext = ac.audioContext
    const workletNode: AudioWorkletNode = ac.audioWorkletNode
    const analyser: AnalyserNode = ac.analyser
    const recognizerProcessor: AudioWorkletNode = ac.recognizerProcessor

    if (!ctx || !workletNode || !analyser || !recognizerProcessor) {
      throw new Error('[AudioControlInjector] AudioControl is not fully initialized')
    }

    if (ctx.state === 'suspended') {
      await ctx.resume()
    }

    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`[AudioControlInjector] fetch failed: ${response.status}`)
    }
    const arrayBuffer = await response.arrayBuffer()
    const audioBuffer = await ctx.decodeAudioData(arrayBuffer)

    const fileSource = ctx.createBufferSource()
    fileSource.buffer = audioBuffer
    fileSource.loop = false

    fileSource.connect(workletNode)
    fileSource.connect(analyser)
    fileSource.connect(recognizerProcessor)
    fileSource.connect(ctx.destination)

    fileSource.addEventListener('ended', () => {
      fileSource.disconnect()
      this.startPersistentSilence()
    })

    fileSource.start(0)
    console.debug('[AudioControlInjector] inject_audio: playback & processing started for', url)
  }
}
