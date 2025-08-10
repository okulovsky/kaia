// message-client.ts

import { Message } from './message.js';

/**
 * Client for interacting with the message API over HTTP.
 */
export class AvatarClient {
  private baseUrl: string;
  private session: string;
  private lastMessageId?: string;

  /**
   * @param baseUrl The base URL of the message service (e.g. "http://localhost:8000").
   * @param session Session identifier to use for all requests (defaults to 'default').
   */
  constructor(baseUrl: string, session: string = 'default') {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
    this.session = session;
    this.lastMessageId = undefined;
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
    msg.envelop.publisher = 'console';
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
   * Updates lastMessageId to the id of the last message received.
   *
   * @param count Optional limit on number of messages.
   * @returns Array of Message instances.
   * @throws Error on non-2xx response.
   */
  async getMessages(count?: number): Promise<Message[]> {
    const url = new URL(`${this.baseUrl}/messages/get`);
    url.searchParams.set('session', this.session);
    if (this.lastMessageId) {
      url.searchParams.set('last_message_id', this.lastMessageId);
    }
    if (count != null) {
      url.searchParams.set('count', String(count));
    }

    const resp = await fetch(url.toString(), { method: 'GET' });
    if (!resp.ok) {
      throw new Error(`getMessages failed: ${resp.status} ${resp.statusText}`);
    }

    const data = (await resp.json()) as any[];
    const messages = data.map(raw => {
      try {
        return Message.fromJson(raw);
      } catch (error) {
        console.error('Failed to parse message:', raw, '\nError:', error);
        throw error;
      }
    });

    if (messages.length > 0) {
      const last = messages[messages.length - 1];
      this.lastMessageId = (last as any).envelop.id;
    }

    return messages;
  }

  /**
   * scroll_to_end
   * Calls the 'last' endpoint to retrieve the most recent message id for the session
   * and updates lastMessageId accordingly.
   *
   * @throws Error on non-2xx HTTP response.
   */
  async scrollToEnd(): Promise<void> {
    const url = new URL(`${this.baseUrl}/messages/last`);
    url.searchParams.set('session', this.session);

    const resp = await fetch(url.toString(), { method: 'GET' });
    if (!resp.ok) {
      throw new Error(`scroll_to_end failed: ${resp.status} ${resp.statusText}`);
    }

    const result = (await resp.json()) as { id: string };
    this.lastMessageId = result.id;
  }

}