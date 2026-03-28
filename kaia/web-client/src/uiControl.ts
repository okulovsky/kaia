/**
 * This module handles UI interaction
 */

export interface IUIControlConfig {
    chatContainerId: string
    pictureContainerId: string
    placeholderImagePath?: string
    proxyUrl?: string
}

export class UIControl {
    config: IUIControlConfig
    placeholderImagePath: string

    chatContainer: HTMLElement
    pictureContainer: HTMLImageElement

    constructor (config: IUIControlConfig) {
        this.config = config
        this.placeholderImagePath = config.placeholderImagePath || 'placeholder.svg'

        const chatContainer = document.getElementById(this.config.chatContainerId) as HTMLDivElement
        const pictureContainer = document.getElementById(this.config.pictureContainerId) as HTMLImageElement

        if (!chatContainer || !pictureContainer || !pictureContainer.parentElement) {
            throw new Error ('Chat or picture container failed to initialize')
        }

        this.chatContainer = chatContainer
        this.pictureContainer = pictureContainer
    }

    private proxiedImageUrl (url: string): string {
        if (!this.config.proxyUrl) return url
        try {
            const u = new URL(url, window.location.origin)
            u.host = this.config.proxyUrl.replace(/^https?:\/\//, '')
            u.protocol = this.config.proxyUrl.startsWith('https') ? 'https:' : 'http:'
            return u.toString()
        } catch {
            return url
        }
    }

    addChatMessage (message: string, options: { avatar?: string, type: string }) {
        const { type = 'from', avatar } = options
        
        const messageEl = document.createElement('div')
        messageEl.className = `chat-message ${type} rounded`

        const contentEl = document.createElement('div')
        contentEl.className = 'chat-content'
        contentEl.textContent = message

        const avatarEl = document.createElement('div')
        avatarEl.className = 'chat-avatar rounded-circle'
        
        if (avatar) {
            avatarEl.style.backgroundImage = `url(${this.proxiedImageUrl(avatar)})`
        } else {
            switch (type) {
                case 'to':
                    avatarEl.innerHTML = '<i class="bi bi-stars"></i>'
                    break
                default:
                    avatarEl.innerHTML = '<i class="bi bi-person"></i>'
            }
        }
        
        if (type !== 'service') {
            messageEl.appendChild(avatarEl)
            messageEl.appendChild(contentEl)
        } else {
            messageEl.appendChild(contentEl)
        }
        
        this.chatContainer.appendChild(messageEl)
        this.chatContainer.scrollTop = this.chatContainer.scrollHeight
    }

    _debugUpdateVolume (volume: number) {
        const volumeValue = document.getElementById('volumeValue')
        const volumeBar = document.getElementById('volumeBar')
        
        if (volumeValue && volumeBar) {
            volumeValue.textContent = volume.toString()
            
            const percentage = Math.min(volume, 100)
            volumeBar.style.width = `${percentage}%`
            
            volumeBar.className = 'progress-bar bg-primary'
        }
    }

    _debugSetThreshold (threshold: number) {
        const thresholdIndicator = document.getElementById('thresholdIndicator')
        const thresholdValue = document.getElementById('thresholdValue')
        
        if (thresholdIndicator) {
            const position = Math.min(threshold, 100)
            thresholdIndicator.style.left = `${position}%`
        }
        
        if (thresholdValue) {
            thresholdValue.textContent = threshold.toString()
        }
    }

    _debugUpdateState (state: string) {
        const stateIndicator = document.getElementById('stateIndicator')
        
        if (stateIndicator) {
            stateIndicator.textContent = state
            
            switch (state) {
                case 'standby':
                    stateIndicator.className = 'badge bg-secondary'
                    break
                case 'open':
                    stateIndicator.className = 'badge bg-info'
                    break
                case 'recording':
                    stateIndicator.className = 'badge bg-danger'
                    break
                case 'playing':
                    stateIndicator.className = 'badge bg-success'
                    break
                default:
                    stateIndicator.className = 'badge bg-secondary'
            }
        }
    }

    changePicture (pictureUrl: string) {
        if (!this.pictureContainer || !this.pictureContainer.src || !this.pictureContainer.parentElement) {
            throw new Error ('Chat or picture container failed to initialize')
        }

        this.pictureContainer.src = this.proxiedImageUrl(pictureUrl)
    }

    clearChat () {
        if (!this.chatContainer) {
            throw new Error('Chat container failed to initialize')
        }

        while (this.chatContainer.firstChild) {
            this.chatContainer.removeChild(this.chatContainer.firstChild)
        }
    }

    clearPicture () {
        if (!this.pictureContainer || !this.pictureContainer.parentElement) {
            throw new Error('Picture container failed to initialize')
        }

        this.pictureContainer.src = this.placeholderImagePath
    }
}