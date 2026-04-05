import { AvatarClient } from './avatarClient.js'
import { Message } from './message.js'

export type Handler = (msg: Message, client: AvatarClient) => Promise<void>;

export class Dispatcher {
  private client: AvatarClient
  private handlers = new Map<string, Handler[]>()
  private running = false

  constructor (client: AvatarClient) {
    this.client = client
  }

  /** Subscribe a handler to any message whose type endsWith this suffix */
  subscribe (suffix: string, handler: Handler): void {
    const list = this.handlers.get(suffix) ?? []
    list.push(handler)
    this.handlers.set(suffix, list)
  }

  /** Start the long-poll loop */
  start (): void {
    if (this.running) return
    this.running = true
    this.client.allowedTypes = [...this.handlers.keys()]
    void this.loop()
  }

  push (msg: Message): void {
    this.client.push(msg).catch(err => console.error('Dispatcher.push failed:', err))
  }

  /** Stop the loop after the current pull completes */
  stop (): void {
    this.running = false
  }

  private async loop (): Promise<void> {
    while (this.running) {
      let msgs: Message[]
      try {
        msgs = await this.client.pull()
      } catch (e) {
        console.error('Dispatcher: fetch failed', e)
        continue
      }

      const handlerPromises: Promise<void>[] = []
      for (const msg of msgs) {
        for (const [suffix, handlers] of this.handlers) {
          if (msg.message_type.endsWith(suffix)) {
            for (const h of handlers) {
              handlerPromises.push(
                  h(msg, this.client).catch(err =>
                      console.error(`Handler for ${suffix} failed:`, err)
                  )
              )
            }
          }
        }
      }
      if (handlerPromises.length > 0) {
        await Promise.allSettled(handlerPromises)
      }
    }
  }

}
