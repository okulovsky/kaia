// image‐handler.ts

import { Dispatcher } from './dispatcher.js';
import { Message }    from './message.js';

/**
 * A handler that listens for "/ImageCommand" messages
 * and writes the base64 payload directly into an <img>.
 */
export class ImageCommandHandler {
  private suffix = '/ImageCommand';

  /**
   * @param dispatcher dispatches incoming Messages
   * @param imgEl      the <img> element to update
   */
  constructor(
    dispatcher: Dispatcher,
    private imgEl: HTMLImageElement
  ) {
    dispatcher.subscribe(this.suffix, this.handle.bind(this));
  }

  private async handle(msg: Message): Promise<void> {
    const fileId: string = msg.payload.file_id;
    const url = `/file-cache/download/${encodeURIComponent(fileId)}`;
    this.imgEl.src = url;
    return;
  }
}
