import { Dispatcher, Message } from '../core/index.js'

/**
 * A handler that listens for "/ImageCommand" messages
 * and writes the base64 payload directly into an <img>.
 */
export class ImageCommandHandler {
  private suffix = '.ImageCommand'
  private imgEl: HTMLImageElement
  private decodeTimeoutInMilliseconds = 200

  /**
   * @param dispatcher dispatches incoming Messages
   * @param imgEl      the <img> element to update
   */
  constructor (
    { dispatcher, imgEl }: { dispatcher: Dispatcher, imgEl: HTMLImageElement }
  ) {
    this.imgEl = imgEl
    dispatcher.subscribe(this.suffix, this.handle.bind(this))
  }

  /**
   * Shows the cached file with the given id in the managed <img>.
   * The returned promise resolves only when the new image is decoded and ready
   * to be painted, so that the caller can uncover the <img> without showing
   * a blank frame or the image that was there before.
   *
   * Until then the element keeps painting the previous image: an <img> that
   * loads a new src reports the old one as complete, which is why the readiness
   * shortcut is taken only when the src is not changing at all.
   */
  show (fileId: string): Promise<void> {
    const url = `/cache/open/${encodeURIComponent(fileId)}`
    if (this.imgEl.getAttribute('src') === url) {
      if (this.imgEl.complete && this.imgEl.naturalWidth > 0) {
        return Promise.resolve()
      }
    } else {
      this.imgEl.src = url
    }
    return this.whenReady()
  }

  /**
   * Resolves when the element is ready to paint what it has been given.
   *
   * decode() is the accurate answer, but a browser that does not render the
   * page - a background tab, a minimized window - may never settle it, so it
   * is given only a short grace period after the image itself has arrived.
   */
  private whenReady (): Promise<void> {
    const loaded = new Promise<void>(resolve => {
      const done = (): void => {
        this.imgEl.removeEventListener('load', done)
        this.imgEl.removeEventListener('error', done)
        resolve()
      }
      this.imgEl.addEventListener('load', done)
      this.imgEl.addEventListener('error', done)
    })
    if (typeof this.imgEl.decode !== 'function') {
      return loaded
    }
    const grace = loaded.then(() => new Promise<void>(
      resolve => window.setTimeout(resolve, this.decodeTimeoutInMilliseconds)
    ))
    return Promise.race([this.imgEl.decode().catch(() => {}), grace])
  }

  private async handle (msg: Message): Promise<void> {
    await this.show(msg.payload.file_id)
  }
}