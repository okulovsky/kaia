import { AvatarClient, Message } from '../core/index.js'

interface TextInputHandlerOptions {
  input: HTMLTextAreaElement
  button: HTMLElement
  client: AvatarClient
}

export class TextInputHandler {
  private input: HTMLTextAreaElement
  private client: AvatarClient

  constructor ({ input, button, client }: TextInputHandlerOptions) {
    this.input = input
    this.client = client

    button.addEventListener('click', () => this.send())
    input.addEventListener('keydown', (e: KeyboardEvent) => {
      if (e.key === 'Enter' && e.ctrlKey) {
        e.preventDefault()
        this.send()
      }
    })
  }

  private send (): void {
    const text = this.input.value.trim()
    const msg = new Message('TextEvent')
    msg.payload = { text }
    this.client.push(msg)
    this.input.value = ''
    this.input.focus()
  }
}
