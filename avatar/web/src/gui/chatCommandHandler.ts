import { Dispatcher, AvatarClient, Message } from '../core/index.js'

interface ChatCommandHandlerOptions {
  dispatcher: Dispatcher
  container: HTMLElement
  baseUrl: string
  client?: AvatarClient
  enableSwiping?: boolean
  enableDeletion?: boolean
}

export class ChatCommandHandler {
  private suffix = '.ChatCommand'
  private deleteSuffix = '.DeleteChatMessagesCommand'
  private container: HTMLElement
  private baseUrl: string
  private client: AvatarClient | undefined
  private enableSwiping: boolean
  private enableDeletion: boolean
  private menu!: HTMLElement

  constructor ({
    dispatcher,
    container,
    baseUrl,
    client,
    enableSwiping = false,
    enableDeletion = false,
  }: ChatCommandHandlerOptions) {
    this.container = container
    this.baseUrl = baseUrl
    this.client = client
    this.enableSwiping = enableSwiping
    this.enableDeletion = enableDeletion

    if (enableDeletion) {
      this.menu = this.createContextMenu()
      document.body.appendChild(this.menu)
      document.addEventListener('click', () => this.hideMenu())
    }

    dispatcher.subscribe(this.suffix, this.handle.bind(this))
    dispatcher.subscribe(this.deleteSuffix, this.handleDelete.bind(this))

    let isDragging = false
    let startScroll = 0
    let startY = 0

    this.container.addEventListener('mousedown', (e: MouseEvent) => {
      isDragging = true
      startScroll = this.container.scrollTop
      startY = e.clientY
      e.preventDefault()
    })

    window.addEventListener('mouseup', () => { isDragging = false })

    this.container.addEventListener('mousemove', (e: MouseEvent) => {
      if (isDragging) {
        this.container.scrollTop = startScroll + (startY - e.clientY)
      }
    })

    this.container.addEventListener('mouseleave', () => { isDragging = false })
  }

  private populateElement (p: HTMLElement, text: string, type: string, avatarId: string | undefined, details: string | undefined, hoverString: string | undefined): void {
    p.className = ''
    switch (type) {
      case 'from_user': p.classList.add('right'); break
      case 'to_user':   p.classList.add('left');  break
      case 'system':    p.classList.add('system'); break
      case 'error':     p.classList.add('error');  break
      default:          p.classList.add('left')
    }

    if (avatarId && (type === 'from_user' || type === 'to_user')) {
      p.style.backgroundImage = `url('${this.baseUrl}${avatarId}')`
    } else {
      p.style.backgroundImage = ''
    }

    p.innerHTML = escapeHtml(text).split('\n').join('<br>')
    p.title = hoverString ?? ''

    if (details) {
      const span = document.createElement('span')
      span.classList.add('chat-details')
      span.textContent = details
      p.appendChild(span)
    }
  }

  private async handle (msg: Message): Promise<void> {
    const payload: any = msg.payload
    const text = String(payload.text ?? '')
    const type = String(payload.type ?? 'to_user')
    const avatarId = payload.sender_avatar_file_id
    const messageId: string | undefined = payload.message_id ?? undefined
    const details: string | undefined = payload.details ?? undefined
    const hoverString: string | undefined = payload.hover_string ?? undefined

    const existing = messageId
      ? this.container.querySelector<HTMLElement>(`[data-message-id="${messageId}"]`)
      : null

    if (existing) {
      this.populateElement(existing, text, type, avatarId, details, hoverString)
      return
    }

    const p = document.createElement('p')
    if (messageId) {
      p.dataset.messageId = messageId
    }

    this.populateElement(p, text, type, avatarId, details, hoverString)

    if (this.enableSwiping && messageId && type === 'to_user') {
      this.attachSwipe(p, messageId)
    }

    if (this.enableDeletion && messageId) {
      this.attachContextMenu(p, messageId)
    }

    this.container.appendChild(p)
    this.container.scrollTop = this.container.scrollHeight
  }

  private async handleDelete (msg: Message): Promise<void> {
    const ids: string[] = (msg.payload as any).ids ?? []
    for (const id of ids) {
      const el = this.container.querySelector(`[data-message-id="${id}"]`)
      if (el) el.remove()
    }
  }

  private attachSwipe (el: HTMLElement, messageId: string): void {
    let touchStartX = 0
    el.addEventListener('touchstart', (e: TouchEvent) => {
      touchStartX = e.touches[0].clientX
    }, { passive: true })
    el.addEventListener('touchend', (e: TouchEvent) => {
      const dx = e.changedTouches[0].clientX - touchStartX
      if (Math.abs(dx) < 50) return
      const eventMsg = new Message('SwipeChatMessageEvent')
      eventMsg.payload = { message_id: messageId, swipe_to_left: dx < 0 }
      this.client?.push(eventMsg)
    }, { passive: true })

    let mouseStartX = 0
    let mouseDown = false
    el.addEventListener('mousedown', (e: MouseEvent) => {
      mouseDown = true
      mouseStartX = e.clientX
      e.stopPropagation()
    })
    window.addEventListener('mouseup', (e: MouseEvent) => {
      if (!mouseDown) return
      mouseDown = false
      const dx = e.clientX - mouseStartX
      if (Math.abs(dx) < 50) return
      const eventMsg = new Message('SwipeChatMessageEvent')
      eventMsg.payload = { message_id: messageId, swipe_to_left: dx < 0 }
      this.client?.push(eventMsg)
    })
  }

  private createContextMenu (): HTMLElement {
    const menu = document.createElement('div')
    menu.classList.add('chat-context-menu')
    const deleteBtn = document.createElement('button')
    deleteBtn.textContent = 'Delete'
    menu.appendChild(deleteBtn)
    menu.addEventListener('click', (e) => e.stopPropagation())
    return menu
  }

  private showMenu (x: number, y: number, messageId: string): void {
    const btn = this.menu.querySelector('button')!
    btn.onclick = () => {
      const eventMsg = new Message('DeleteChatMessageEvent')
      eventMsg.payload = { message_id: messageId }
      this.client?.push(eventMsg)
      this.hideMenu()
    }
    this.menu.style.left = `${x}px`
    this.menu.style.top = `${y}px`
    this.menu.classList.add('visible')
    const rect = this.menu.getBoundingClientRect()
    if (rect.right > window.innerWidth) this.menu.style.left = `${x - rect.width}px`
    if (rect.bottom > window.innerHeight) this.menu.style.top = `${y - rect.height}px`
  }

  private hideMenu (): void {
    this.menu.classList.remove('visible')
  }

  private attachContextMenu (el: HTMLElement, messageId: string): void {
    el.addEventListener('contextmenu', (e: MouseEvent) => {
      e.preventDefault()
      e.stopPropagation()
      this.showMenu(e.clientX, e.clientY, messageId)
    })

    let longPressTimer: ReturnType<typeof setTimeout> | null = null
    el.addEventListener('touchstart', () => {
      longPressTimer = setTimeout(() => {
        const rect = el.getBoundingClientRect()
        this.showMenu(rect.left, rect.bottom + 4, messageId)
      }, 500)
    }, { passive: true })
    el.addEventListener('touchend', () => {
      if (longPressTimer !== null) { clearTimeout(longPressTimer); longPressTimer = null }
    }, { passive: true })
    el.addEventListener('touchmove', () => {
      if (longPressTimer !== null) { clearTimeout(longPressTimer); longPressTimer = null }
    }, { passive: true })
  }
}

function escapeHtml (str: string): string {
  return str.replace(/[&<>"']/g, c => {
    switch (c) {
      case '&': return '&amp;'
      case '<': return '&lt;'
      case '>': return '&gt;'
      case '"': return '&quot;'
      case "'": return '&#39;'
      default: return c
    }
  })
}
