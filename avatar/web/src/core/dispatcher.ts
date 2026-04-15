import { AvatarClient } from './avatarClient.js'
import { Message } from './message.js'

export type Handler = (msg: Message, client: AvatarClient) => Promise<void>;

export class Dispatcher {
  private client: AvatarClient
  private handlers = new Map<string, Handler[]>()
  private running = false
  private abortController: AbortController | null = null

  constructor (client: AvatarClient) {
    this.client = client
  }

  private syncAllowedTypes (): void {
    this.client.allowedTypes = [...this.handlers.keys()]
    if (this.running) {
      this.abortController?.abort()
    }
  }

  /** Subscribe a handler to any message whose type endsWith this suffix */
  subscribe (suffix: string, handler: Handler): Handler {
    const list = this.handlers.get(suffix) ?? []
    list.push(handler)
    this.handlers.set(suffix, list)
    this.syncAllowedTypes()
    return handler
  }

  /** Unsubscribe a previously subscribed handler */
  unsubscribe (suffix: string, handler: Handler): void {
    const list = this.handlers.get(suffix)
    if (!list) return
    const idx = list.indexOf(handler)
    if (idx !== -1) list.splice(idx, 1)
    if (list.length === 0) this.handlers.delete(suffix)
    this.syncAllowedTypes()
  }

  /** Start the long-poll loop */
  start (): void {
    if (this.running) return
    this.running = true
    this.syncAllowedTypes()
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
      this.abortController = new AbortController()
      let msgs: Message[]
      try {
        const result = await this.client.pullWithDetails(undefined, undefined, this.abortController.signal)
        if (result.missingId) {
          window.location.reload()
          return
        }
        msgs = result.messages
      } catch (e) {
        if (e instanceof DOMException && e.name === 'AbortError') continue
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
