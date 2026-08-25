import { Dispatcher, Message } from '../core/index.js'

/**
 * A handler that listens for "/ImageCommand" messages
 * and writes the base64 payload directly into an <img>.
 */
export class ImageCommandHandler {
  private suffix = '.ImageCommand'
  private imgEl: HTMLImageElement

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
   * The returned promise resolves once the image is ready to be painted, so
   * that the caller can uncover the <img> without showing a blank frame.
   */
  show (fileId: string): Promise<void> {
    const url = `/cache/open/${encodeURIComponent(fileId)}`
    if (this.imgEl.getAttribute('src') !== url) {
      this.imgEl.src = url
    }
    if (this.imgEl.complete && this.imgEl.naturalWidth > 0) {
      return Promise.resolve()
    }
    if (typeof this.imgEl.decode === 'function') {
      return this.imgEl.decode().catch(() => {})
    }
    return new Promise<void>(resolve => {
      const done = (): void => {
        this.imgEl.removeEventListener('load', done)
        this.imgEl.removeEventListener('error', done)
        resolve()
      }
      this.imgEl.addEventListener('load', done)
      this.imgEl.addEventListener('error', done)
    })
  }

  private async handle (msg: Message): Promise<void> {
    await this.show(msg.payload.file_id)
  }
}