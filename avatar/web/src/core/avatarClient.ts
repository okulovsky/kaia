import { Message, Envelop } from './message.js'

interface IAvatarClientConfig {
  baseUrl: string
  session?: string
  allowedTypes?: string[] | null
}

export class AvatarClient {
  private baseUrl: string
  private session: string
  allowedTypes: string[] | null
  lastId?: string

  constructor (config: IAvatarClientConfig) {
    this.baseUrl = config.baseUrl.replace(/\/+$/, '')
    this.session = config.session ?? 'default'
    this.allowedTypes = config.allowedTypes ?? null
    this.lastId = undefined
  }

  async push (msg: Message): Promise<void> {
    const url = `${this.baseUrl}/messaging/put`
    msg.envelop.publisher = 'console'
    const body = {
      message: {
        session: this.session,
        content_type: msg.message_type,
        envelop: msg.envelop,
        content: msg.payload,
      },
    }
    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!resp.ok) {
      throw new Error(`push failed: ${resp.status} ${resp.statusText}`)
    }
  }

  async pullWithDetails (timeout_in_seconds?: number | null, max_messages?: number | null, signal?: AbortSignal): Promise<{ messages: Message[], missingId: boolean }> {
    const url = new URL(`${this.baseUrl}/messaging/get/${encodeURIComponent(this.session)}`)
    if (this.lastId !== undefined) {
      url.searchParams.set('last_id', this.lastId)
    }
    if (max_messages !== undefined && max_messages !== null) {
      url.searchParams.set('max_messages', String(max_messages))
    }
    if (timeout_in_seconds !== undefined && timeout_in_seconds !== null) {
      url.searchParams.set('timeout_in_seconds', String(timeout_in_seconds))
    }

    const resp = await fetch(url.toString(), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ allowed_types: this.allowedTypes }),
      signal,
    })
    if (!resp.ok) {
      throw new Error(`pull failed: ${resp.status} ${resp.statusText}`)
    }

    const data = await resp.json()
    const messages = (data.messages as any[]).map(raw => {
      try {
        return new Message(raw.content_type, Envelop.fromJson(raw.envelop), raw.content ?? {})
      } catch (error) {
        console.error('Failed to parse message:', raw, '\nError:', error)
        throw error
      }
    })

    if (messages.length > 0) {
      this.lastId = messages[messages.length - 1].envelop.id
    }

    return { messages, missingId: !!data.missing_id }
  }

  async pull (timeout_in_seconds?: number | null, max_messages?: number | null, signal?: AbortSignal): Promise<Message[]> {
    return (await this.pullWithDetails(timeout_in_seconds, max_messages, signal)).messages
  }

  async tail (count: number): Promise<Message[]> {
    const url = `${this.baseUrl}/messaging/tail/${encodeURIComponent(this.session)}/${count}`
    const resp = await fetch(url, { method: 'POST' })
    if (!resp.ok) {
      throw new Error(`tail failed: ${resp.status} ${resp.statusText}`)
    }
    const data = await resp.json()
    return (data.messages as any[]).map(raw =>
      new Message(raw.content_type, Envelop.fromJson(raw.envelop), raw.content ?? {})
    )
  }

  setLastId (lastId: string | null | undefined): void {
    this.lastId = lastId ?? undefined
  }

  async scrollToEnd (): Promise<void> {
    const messages = await this.tail(1)
    if (messages.length > 0) {
      this.lastId = messages[messages.length - 1].envelop.id
    } else {
      this.lastId = undefined
    }
  }
}
