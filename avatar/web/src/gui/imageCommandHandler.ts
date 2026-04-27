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

  private async handle (msg: Message): Promise<void> {
    const fileId: string = msg.payload.file_id
    const url = `/cache/open/${encodeURIComponent(fileId)}`
    this.imgEl.src = url
    return
  }
}