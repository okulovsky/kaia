import { AvatarClient } from './client.js';
import { Message } from './message.js';

export type Handler = (msg: Message, client: AvatarClient) => Promise<void>;

export class Dispatcher {
  private client: AvatarClient;
  private rateMs: number;
  private handlers = new Map<string, Handler[]>();
  private timerId?: number;

  /**
   * @param client  your AvatarClient instance
   * @param updateRateInSeconds  poll interval
   */
  constructor(client: AvatarClient, updateRateInSeconds: number) {
    this.client = client;
    this.rateMs = updateRateInSeconds * 1000;
  }

  /** Subscribe a handler to any message whose type endsWith this suffix */
  subscribe(suffix: string, handler: Handler): void {
    const list = this.handlers.get(suffix) ?? [];
    list.push(handler);
    this.handlers.set(suffix, list);
  }

  /** Start polling & dispatching */
  start(): void {
    this.timerId = window.setInterval(() => void this.tick(), this.rateMs);
  }

  /** Stop polling */
  stop(): void {
    if (this.timerId != null) {
      clearInterval(this.timerId);
      this.timerId = undefined;
    }
  }

  /** One polling round */
  private async tick(): Promise<void> {
    let msgs: Message[];
    try {
      msgs = await this.client.getMessages();
    } catch (e) {
      console.error('Dispatcher: fetch failed', e);
      return;
    }

    for (const msg of msgs) {
      for (const [suffix, handlers] of this.handlers) {
        if (msg.message_type.endsWith(suffix)) {
          for (const h of handlers) {
            // fire & forget each handler, catch errors
            h(msg, this.client).catch(err =>
              console.error(`Handler for ${suffix} failed:`, err)
            );
          }
        }
      }
    }
  }
}
