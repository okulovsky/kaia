import { AvatarClient } from './avatarClient.js'

export class ControlPanelController {
  private trigger: HTMLDivElement
  private panel: HTMLDivElement
  private overlay: HTMLDivElement
  private client: AvatarClient
  private isOpen: boolean = false
  private buttons: HTMLButtonElement[] = []

  constructor (trigger: HTMLDivElement, panel: HTMLDivElement, overlay: HTMLDivElement, client: AvatarClient) {
    this.trigger = trigger
    this.panel = panel
    this.overlay = overlay
    this.client = client

    this.panel.innerHTML = ''

    this.addButton('📊', () => this.loadPageInOverlay('/phonix-monitor/'))
    this.addButton('↺', () => location.reload())
    this.addButton('🗗', () => this.toggleOverlay())
    this.addButton('❌',  () => window.close())

    this.trigger.addEventListener('click', () => this.togglePanel())
  }

  addDebugPanel (
      label: string,
      panel: any
  ): void {
      this.addButton(label, ()=>this.startPanel(panel))
  }

  private startOverlay () {
    this.overlay.className = ''
    this.overlay.classList.add('overlay-full')
    this.overlay.style.display = ''
    this.overlay.innerHTML = ''
  }

  private startPanel (panel: any) {
      this.startOverlay()
      panel.setPanel(this.overlay)
      panel.start()
  }

  private addButton (
    label: string,
    onClick: () => void
  ): void {
    const btn = document.createElement('button')
    btn.textContent = label
    btn.classList.add('system-btn')
    btn.addEventListener('click', () => {
      onClick()
      this.hidePanel()
    })
    this.panel.appendChild(btn)
  }

private async loadPageInOverlay (url: string): Promise<void> {
  this.startOverlay()
  try {
    const response = await fetch(url, { method: 'HEAD' })

    if (!response.ok) {
      throw new Error(`Loading error: ${response.status} ${response.statusText}`)
    }

    const iframe = document.createElement('iframe')
    iframe.src = url
    iframe.style.width = '100%'
    iframe.style.height = '100%'
    iframe.style.border = '0'
    this.overlay.appendChild(iframe)

  } catch (err) {
    const message = err instanceof Error
      ? err.message
      : String(err)
    this.overlay.textContent = message
  }
}

  private toggleOverlay (): void {
    const isHidden = window.getComputedStyle(this.overlay).display === 'none'
    if (isHidden) {
      this.overlay.style.display = ''
    } else {
      this.overlay.style.display = 'none'
    }
  }

  private togglePanel (): void {
    this.isOpen ? this.hidePanel() : this.showPanel()
  }

  private showPanel (): void {
    this.panel.classList.add('open')
    this.isOpen = true
  }

  private hidePanel (): void {
    this.panel.classList.remove('open')
    this.isOpen = false
  }
}
