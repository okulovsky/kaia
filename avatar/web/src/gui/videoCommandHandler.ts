import { Dispatcher, Message } from '../core/index.js'
import { ImageCommandHandler } from './imageCommandHandler.js'

/** Thrown into a pending playback when a newer VideoCommand arrives. */
class PlaybackAborted extends Error {}

/**
 * A handler that listens for "/VideoCommand" messages and plays the listed
 * videos one after another, on top of the image.
 *
 * Every video is downloaded into memory as a Blob before it is played. While a
 * video is playing, the next one is already being downloaded, and the memory of
 * a video is released as soon as it has been played. When the last video ends,
 * the optional final_image is handed over to the ImageCommandHandler.
 *
 * To keep the transitions seamless, the handler owns two stacked <video> layers
 * inside the container. Only one of them is visible at a time: the next video is
 * loaded into the hidden layer and is only brought to the front once its first
 * frame can be painted, so nothing blank is ever shown in between.
 */
export class VideoCommandHandler {
  private suffix = '.VideoCommand'
  private layers: HTMLVideoElement[]
  private layerUrls: (string | null)[] = [null, null]
  private layerDetach: (() => void)[] = [() => {}, () => {}]
  private visible = -1
  private imageHandler: ImageCommandHandler | null
  private base: string
  private generation = 0
  private abort: (() => void) | null = null

  /**
   * @param dispatcher   dispatches incoming Messages
   * @param container    the element to put the video layers into; it has to be positioned
   * @param imageHandler the handler that shows the final image, if any
   * @param baseUrl      prefix for the /cache/open urls
   * @param className    the class of the video layers, so that the page can style them
   */
  constructor (
    { dispatcher, container, imageHandler, baseUrl = '', className = 'video-layer' }: {
      dispatcher: Dispatcher,
      container: HTMLElement,
      imageHandler?: ImageCommandHandler,
      baseUrl?: string,
      className?: string
    }
  ) {
    this.layers = [this.createLayer(container, className), this.createLayer(container, className)]
    this.imageHandler = imageHandler ?? null
    this.base = baseUrl.replace(/\/+$/, '')
    dispatcher.subscribe(this.suffix, this.handle.bind(this))
  }

  private createLayer (container: HTMLElement, className: string): HTMLVideoElement {
    const layer = document.createElement('video')
    layer.className = className
    layer.muted = true
    layer.playsInline = true
    layer.preload = 'auto'
    layer.style.position = 'absolute'
    layer.style.left = '0'
    layer.style.top = '0'
    layer.style.width = '100%'
    layer.style.height = '100%'
    layer.style.opacity = '0'
    container.appendChild(layer)
    return layer
  }

  private videoUrl (fileId: string): string {
    return `${this.base}/cache/open/${encodeURIComponent(fileId)}`
  }

  /** Downloads a video into memory and returns an object url for it. */
  private async load (fileId: string): Promise<string> {
    const url = this.videoUrl(fileId)
    const resp = await fetch(url)
    if (!resp.ok) throw new Error(`[VideoCommandHandler] fetch failed ${url}: ${resp.status}`)
    return URL.createObjectURL(await resp.blob())
  }

  /** Loads a video into a hidden layer and waits until its first frame can be painted. */
  private prepare (index: number, objectUrl: string): Promise<void> {
    const layer = this.layers[index]
    this.release(index)
    this.layerUrls[index] = objectUrl
    return new Promise<void>((resolve, reject) => {
      const cleanup = (): void => {
        layer.removeEventListener('loadeddata', onLoaded)
        layer.removeEventListener('error', onError)
        this.layerDetach[index] = () => {}
      }
      const onLoaded = (): void => {
        cleanup()
        requestAnimationFrame(() => resolve())
      }
      const onError = (): void => {
        cleanup()
        reject(new Error(`[VideoCommandHandler] cannot load a video into layer ${index}`))
      }
      this.layerDetach[index] = cleanup
      layer.addEventListener('loadeddata', onLoaded)
      layer.addEventListener('error', onError)
      layer.src = objectUrl
      layer.load()
    })
  }

  /** Plays a prepared layer, resolving when it has ended. */
  private playToEnd (index: number): Promise<void> {
    const layer = this.layers[index]
    return new Promise<void>((resolve, reject) => {
      const cleanup = (): void => {
        layer.removeEventListener('ended', onEnded)
        layer.removeEventListener('error', onError)
        this.layerDetach[index] = () => {}
      }
      const onEnded = (): void => { cleanup(); resolve() }
      const onError = (): void => {
        cleanup()
        reject(new Error(`[VideoCommandHandler] playback failed in layer ${index}`))
      }
      this.layerDetach[index] = cleanup
      layer.addEventListener('ended', onEnded)
      layer.addEventListener('error', onError)
      void layer.play().catch(() => onError())
    })
  }

  /** Brings a prepared layer to the front and frees the one it replaces. */
  private reveal (index: number): void {
    this.layers[index].style.opacity = '1'
    const other = 1 - index
    this.layers[other].style.opacity = '0'
    this.release(other)
    this.visible = index
  }

  private hideAll (): void {
    for (let index = 0; index < this.layers.length; index++) {
      this.layers[index].style.opacity = '0'
      this.release(index)
    }
    this.visible = -1
  }

  /** Detaches whatever a layer holds and frees its memory. */
  private release (index: number): void {
    const layer = this.layers[index]
    this.layerDetach[index]()
    if (!layer.paused) layer.pause()
    if (layer.hasAttribute('src')) {
      layer.removeAttribute('src')
      layer.load()
    }
    const url = this.layerUrls[index]
    if (url !== null) {
      URL.revokeObjectURL(url)
      this.layerUrls[index] = null
    }
  }

  private hiddenLayer (): number {
    return this.visible === 0 ? 1 : 0
  }

  private async handle (msg: Message): Promise<void> {
    const videos: string[] = msg.payload.videos ?? []
    const finalImage: string | null = msg.payload.final_image ?? null
    const gen = ++this.generation
    this.abort?.()
    void this.run(videos, finalImage, gen)
  }

  private async run (videos: string[], finalImage: string | null, gen: number): Promise<void> {
    let abortReject: (reason: unknown) => void = () => {}
    const aborted = new Promise<never>((_, reject) => { abortReject = reject })
    aborted.catch(() => {})
    const myAbort = (): void => abortReject(new PlaybackAborted())
    this.abort = myAbort
    const race = <T>(promise: Promise<T>): Promise<T> => Promise.race([promise, aborted])

    let pending: Promise<string> | null = null
    try {
      let target = -1
      if (videos.length > 0) {
        const url = await race(this.load(videos[0]))
        target = this.hiddenLayer()
        await race(this.prepare(target, url))
        this.reveal(target)
      }
      for (let i = 0; i < videos.length; i++) {
        pending = i + 1 < videos.length ? this.load(videos[i + 1]) : null
        const playing = this.playToEnd(target)
        let nextTarget = -1
        if (pending !== null) {
          const url = await race(pending)
          pending = null
          nextTarget = 1 - target
          await race(this.prepare(nextTarget, url))
        }
        await race(playing)
        if (nextTarget < 0) break
        this.reveal(nextTarget)
        target = nextTarget
      }
      if (gen !== this.generation) return
      if (finalImage !== null && this.imageHandler !== null) {
        await race(this.imageHandler.show(finalImage))
      }
      if (gen !== this.generation) return
      this.hideAll()
    } catch (e) {
      if (!(e instanceof PlaybackAborted)) {
        console.error('[VideoCommandHandler]', e)
        if (gen === this.generation) this.hideAll()
      }
    } finally {
      if (pending !== null) void pending.then(url => URL.revokeObjectURL(url), () => {})
      if (this.abort === myAbort) this.abort = null
    }
  }
}
