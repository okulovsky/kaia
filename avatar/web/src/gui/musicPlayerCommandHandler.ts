import { Dispatcher, AvatarClient, Message } from '../core/index.js'

export class MusicPlayerCommandHandler {
  private suffix = '.MusicStatusCommand'
  private div: HTMLElement
  private client: AvatarClient

  private caption: HTMLElement
  private pauseBtn: HTMLButtonElement
  private resumeBtn: HTMLButtonElement
  private prevBtn: HTMLButtonElement
  private nextBtn: HTMLButtonElement
  private stopBtn: HTMLButtonElement

  constructor (
    { dispatcher, div, client }: { dispatcher: Dispatcher, div: HTMLElement, client: AvatarClient }
  ) {
    this.div = div
    this.client = client

    this.caption = document.createElement('div')
    this.caption.className = 'music-player-caption'
    div.appendChild(this.caption)

    this.prevBtn   = this.makeButton('⏮', 'MusicPreviousButtonEvent')
    this.pauseBtn  = this.makeButton('⏸', 'MusicPauseButtonEvent')
    this.resumeBtn = this.makeButton('▶', 'MusicResumeButtonEvent')
    this.nextBtn   = this.makeButton('⏭', 'MusicNextButtonEvent')
    this.stopBtn   = this.makeButton('⏹', 'MusicStopButtonEvent')

    div.style.display = 'none'
    dispatcher.subscribe(this.suffix, this.handle.bind(this))
  }

  private makeButton (label: string, eventType: string): HTMLButtonElement {
    const btn = document.createElement('button')
    btn.className = 'music-player-button'
    btn.textContent = label
    btn.addEventListener('click', () => this.client.push(new Message(eventType)))
    this.div.appendChild(btn)
    return btn
  }

  private async handle (msg: Message): Promise<void> {
    const status = msg.payload.status

    if (!status?.has_music) {
      this.div.style.display = 'none'
      return
    }

    this.div.style.display = ''
    this.caption.textContent = status.current_track_summary ?? ''

    const playing: boolean = status.playing
    this.pauseBtn.disabled  = !playing
    this.resumeBtn.disabled = playing
    this.prevBtn.disabled   = false
    this.nextBtn.disabled   = false
    this.stopBtn.disabled   = false
  }
}
