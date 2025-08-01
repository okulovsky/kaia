// button-grid-handler.ts

import { Dispatcher }     from './dispatcher.js';
import { AvatarClient }   from './client.js';
import { Message }        from './message.js';

/**
 * Renders a ButtonGrid (suffix '/ButtonGrid') into a container DIV,
 * laying out buttons in a CSS grid.  Buttons whose `button_feedback` is null
 * are disabled; others, when clicked, send a ButtonPressedEvent back to the server.
 */
export class ButtonGridHandler {
  private suffix = '/ButtonGrid';

  /**
   * @param dispatcher  your Dispatcher instance
   * @param container   the DIV where buttons go
   * @param client      AvatarClient used to send ButtonPressedEvent
   */
  constructor(
    dispatcher: Dispatcher,
    private container: HTMLElement,
    private client: AvatarClient
  ) {
    dispatcher.subscribe(this.suffix, this.handle.bind(this));
  }

  private async handle(msg: Message): Promise<void> {
    const payload: any = msg.payload;
    const elements: any[] | null = payload.elements ?? null;

    // hide the container if no grid
    if (!elements) {
      this.container.style.display = 'none';
      return;
    }

    // show & clear
    this.container.style.display = '';
    this.container.innerHTML = '';

    // compute number of columns
    const colCount = elements.reduce((max, el) => {
      const span = el.column_span ?? 1;
      return Math.max(max, el.column + span);
    }, 0);

    Object.assign(this.container.style, {
      display: 'grid',
      gridTemplateColumns: `repeat(${colCount}, 1fr)`,
      gap: '8px'
    });

    // render each button
    for (const el of elements) {
      const btn = document.createElement('button');
      btn.textContent = String(el.text);

      // grid position
      btn.style.gridRowStart    = String(el.row + 1);
      btn.style.gridColumnStart = String(el.column + 1);
      if (el.row_span)    btn.style.gridRowEnd    = `span ${el.row_span}`;
      if (el.column_span) btn.style.gridColumnEnd = `span ${el.column_span}`;

      // wire up click/send event or disable
      if (el.button_feedback == null) {
        btn.disabled = true;
      } else {
        btn.addEventListener('click', () => {
          // build and send the ButtonPressedEvent
          const eventMsg = new Message('ButtonPressedEvent');
          eventMsg.payload = { button_feedback: el.button_feedback };
          this.client.addMessage(eventMsg);
        });
      }

      this.container.appendChild(btn);
    }
  }
}