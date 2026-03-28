/**
 * Generate a new unique ID (UUID v4) for Envelop.id
 */
function _newId (): string {
  return typeof crypto !== 'undefined' && crypto.randomUUID
    ? crypto.randomUUID()
    : Math.random().toString(36).slice(2, 10)
}

/**
 * Envelope metadata class with utility methods for metadata manipulation.
 */
export class Envelope {
  id: string
  reply_to: string | null
  confirmation_for: string[] | null
  timestamp: string
  publisher: string | null
  confirmation_stack: string[]

  /**
   * @param id            Unique envelope ID
   * @param reply_to      ID of the message this envelope replies to
   * @param confirmation_for  List of message IDs this envelope confirms
   * @param timestamp     ISO timestamp string
   * @param publisher     Publisher identifier
   * @param confirmation_stack  Stack of propagated confirmation IDs
   */
  constructor (
    id: string = _newId(),
    reply_to: string | null = null,
    confirmation_for: string[] | null = null,
    timestamp: string = new Date().toISOString(),
    publisher: string | null = null,
    confirmation_stack: string[] = []
  ) {
    this.id = id
    this.reply_to = reply_to
    this.confirmation_for = confirmation_for
    this.timestamp = timestamp
    this.publisher = publisher
    this.confirmation_stack = confirmation_stack
  }

  /**
   * Construct an Envelope from a raw JSON object, validating required fields.
   */
  static fromJson (raw: any): Envelope {
    if (typeof raw !== 'object' || raw === null) {
      throw new TypeError('Envelope.fromJson: raw must be an object')
    }

    const {
      id,
      reply_to = null,
      confirmation_for = null,
      timestamp,
      publisher = null,
      confirmation_stack = []
    } = raw

    if (typeof id !== 'string') {
      throw new TypeError('Envelope.fromJson: id must be a string')
    }

    if (reply_to !== null && typeof reply_to !== 'string') {
      throw new TypeError('Envelope.fromJson: reply_to must be a string or null')
    }

    if (confirmation_for !== null) {
      if (!Array.isArray(confirmation_for) || !confirmation_for.every(x => typeof x === 'string')) {
        throw new TypeError('Envelope.fromJson: confirmation_for must be string[] or null')
      }
    }

    if (typeof timestamp !== 'string') {
      throw new TypeError('Envelope.fromJson: timestamp must be a string')
    }

    if (publisher !== null && typeof publisher !== 'string') {
      throw new TypeError('Envelope.fromJson: publisher must be a string or null')
    }

    if (!Array.isArray(confirmation_stack) || !confirmation_stack.every(x => typeof x === 'string')) {
      throw new TypeError('Envelope.fromJson: confirmation_stack must be string[]')
    }

    return new Envelope(id, reply_to, confirmation_for, timestamp, publisher, confirmation_stack)
  }
}

/**
 * Message/command class with methods for modification workflows.
 */
export class Message {
  message_type: string
  envelope: Envelope
  payload: Record<string, any>

  /**
   * @param message_type  The type of this message
   * @param envelope       Envelope metadata
   * @param payload       Arbitrary payload dictionary
   */
  constructor (
    message_type: string,
    envelope: Envelope = new Envelope(),
    payload: Record<string, any> = {}
  ) {
    this.message_type = message_type
    this.envelope = envelope
    this.payload = payload
  }

  /**
   * Construct a Message from a raw JSON object, validating required fields.
   */
  static fromJson (raw: any): Message {
    if (typeof raw !== 'object' || raw === null) {
      throw new TypeError('Message.fromJson: raw must be an object')
    }

    const {
      message_type,
      envelope: rawEnv,
      payload
    } = raw

    if (typeof message_type !== 'string') {
      throw new TypeError('Message.fromJson: message_type must be a string')
    }

    const env = Envelope.fromJson(rawEnv)

    if (typeof payload !== 'object' || payload === null) {
      throw new TypeError('Message.fromJson: payload must be an object')
    }

    return new Message(message_type, env, payload)
  }

  /** Marks this message as a reply to another message. */
  asReplyTo (message: Message): this {
    this.envelope.reply_to = message.envelope.id
    return this
  }

  /** Sets confirmation_for to one or more message IDs. */
  asConfirmationFor (message: Message | string | Iterable<string>): this {
    let ids: string[]
    if (message instanceof Message) {
      ids = [message.envelope.id, ...(message.envelope.confirmation_stack ?? [])]
    } else if (typeof message === 'string') {
      ids = [message]
    } else {
      ids = Array.from(message)
      if (!ids.every(id => typeof id === 'string')) {
        throw new Error('Each element in confirmation_for must be a string')
      }
    }
    this.envelope.confirmation_for = ids
    return this
  }

  /** Propagates confirmation by updating the confirmation_stack. */
  asPropagationConfirmationTo (message: Message): this {
    this.envelope.confirmation_stack = [
      message.envelope.id,
      ...(message.envelope.confirmation_stack ?? []),
    ]
    return this
  }
}
