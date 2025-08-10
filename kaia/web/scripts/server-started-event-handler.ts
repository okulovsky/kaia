// server-start-handler.ts

import { Dispatcher } from './dispatcher.js';
import { Message }    from './message.js';

/**
 * A handler that listens for "/ServerStartEvent" messages
 * and reloads the current page.
 */
export class ServerStartedEventHandler {
  private suffix = '/ServerStartedEvent';

  /**
   * @param dispatcher dispatches incoming Messages
   */
  constructor(dispatcher: Dispatcher) {
    dispatcher.subscribe(this.suffix, this.handle.bind(this));
  }

  private async handle(_msg: Message): Promise<void> {
    window.location.reload();
  }
}