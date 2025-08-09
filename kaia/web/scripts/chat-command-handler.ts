// chat-handler.ts

import { Dispatcher } from './dispatcher.js';
import { Message }    from './message.js';

/**
 * A handler that listens for messages ending with '/ChatCommand'
 * and renders them into a chat container, plus enables
 * click‑and‑drag scrolling.
 */
export class ChatCommandHandler {
  private suffix = '/ChatCommand';

  /**
   * @param dispatcher  your Dispatcher instance
   * @param container   the HTML element (e.g. a <div>) to append chat <p>’s to
   * @param baseUrl     base URL to prepend to avatar paths
   */
  constructor(
    dispatcher: Dispatcher,
    private container: HTMLElement,
    private baseUrl: string
  ) {
    // subscribe to ChatCommand messages
    dispatcher.subscribe(this.suffix, this.handle.bind(this));

    // install click‑and‑drag scrolling
    let isDragging = false;
    let startScroll = 0;
    let startY = 0;

    this.container.addEventListener('mousedown', (e: MouseEvent) => {
      isDragging = true;
      startScroll = this.container.scrollTop;
      startY = e.clientY;
      // prevent text selection while dragging
      e.preventDefault();
    });

    window.addEventListener('mouseup', () => {
      isDragging = false;
    });

    this.container.addEventListener('mousemove', (e: MouseEvent) => {
      if (isDragging) {
        this.container.scrollTop = startScroll + (startY - e.clientY);
      }
    });

    this.container.addEventListener('mouseleave', () => {
      isDragging = false;
    });
  }

  private async handle(msg: Message): Promise<void> {
    const payload: any = msg.payload;
    const text = String(payload.text ?? '');
    const type = String(payload.type ?? 'to_user');
    const avatarId = payload.sender_avatar_file_id;

    const p = document.createElement('p');
    // alignment & styling
    switch (type) {
      case 'from_user': p.classList.add('right'); break;
      case 'to_user':   p.classList.add('left');  break;
      case 'system':
        p.classList.add('system');
        break;
      case 'error':
        p.classList.add('error');
        break;
      default:
        p.classList.add('left');
    }

    if (avatarId && (type === 'from_user' || type === 'to_user')) {
      p.style.backgroundImage = `url('${this.baseUrl}${avatarId}')`;
    }

    // replace \n with <br>
    p.innerHTML = escapeHtml(text).split('\n').join('<br>');

    this.container.appendChild(p);
    this.container.scrollTop = this.container.scrollHeight;
  }
}

function escapeHtml(str: string): string {
  return str.replace(/[&<>"']/g, c => {
    switch (c) {
      case '&': return '&amp;';
      case '<': return '&lt;';
      case '>': return '&gt;';
      case '"': return '&quot;';
      case "'": return '&#39;';
      default: return c;
    }
  });
}
