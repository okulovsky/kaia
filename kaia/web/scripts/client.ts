// message-client.ts

import { Message } from './message.js';

/**
 * Client for interacting with the message API over HTTP.
 */
export class AvatarClient {
  private baseUrl: string;
  private session: string;

  /**
   * @param baseUrl The base URL of the message service (e.g. "http://localhost:8000").
   * @param session Session identifier to use for all requests (defaults to 'default').
   */
  constructor(baseUrl: string, session: string = 'default') {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
    this.session = session;
  }

  /**
   * POST /add-message
   * Sends a full Message instance to the server.
   *
   * @param msg  A Message object (must have message_type, envelop, payload).
   * @throws Error on non-2xx HTTP response.
   */
  async addMessage(msg: Message): Promise<void> {
    const url = `${this.baseUrl}/messages/add`;
    msg.envelop.publisher='console';
    const body = {
      message_type: msg.message_type,
      session: this.session,
      envelop: msg.envelop,
      payload: msg.payload,
    };

    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!resp.ok) {
      throw new Error(`addMessage failed: ${resp.status} ${resp.statusText}`);
    }
  }

  /**
   * GET /get-messages
   * Uses the session provided in constructor.
   *
   * @param lastMessageId Optional last_message_id for pagination.
   * @param count         Optional limit on number of messages.
   * @returns Array of Message instances.
   * @throws Error on non-2xx response.
   */
  async getMessages(lastMessageId?: string, count?: number): Promise<Message[]> {
    const url = new URL(`${this.baseUrl}/messages/get`);
    url.searchParams.set('session', this.session);
    if (lastMessageId != null) {
      url.searchParams.set('last_message_id', lastMessageId);
    }
    if (count != null) {
      url.searchParams.set('count', String(count));
    }

    const resp = await fetch(url.toString(), { method: 'GET' });
    if (!resp.ok) {
      throw new Error(`getMessages failed: ${resp.status} ${resp.statusText}`);
    }

    const data = (await resp.json()) as any[];
    // Use the static fromJson to validate and create each Message
    return data.map(raw => Message.fromJson(raw));
  }
}
