export interface IAudioControlClientConfig {
    baseUrl: string
    session?: string
}

/**
 * Client for interacting with the message API over HTTP.
 */
export class AudioControlClient {
    private baseUrl: string
    private session: string

    /**
     * @param config
     */
    constructor (config: IAudioControlClientConfig) {
        this.baseUrl = config.baseUrl.replace(/\/+$/, '')
        this.session = config.session ?? 'default'
    }

    /**
     * Uploads audio chunk
     * @param index
     * @param audioChunks
     */
    async uploadAudioChunk ( index: number, audioChunks: Blob[] ) {
        if (index === undefined || !Array.isArray(audioChunks)) {
            throw new Error('[api] audio chunk index is undefined, or audio chunks is not an array')
        }

        const formData = new FormData()
        formData.append('client_id', this.session)
        formData.append('index', index.toString())
        formData.append('blob', new Blob(audioChunks, { type: 'audio/wav' }))

        const url = `/audio`

        return this._sendRequest(url, {
            method: 'POST',
            body: formData
        })
    }

    /**
     * Invokes `sendConfirmationAudio`
     * @param path
     */
    async sendConfirmationAudio (path: string) {
        const url = `/kaia/command/${this.session}/confirmation_audio`
        const filename = path.split('/').pop()
        return this._sendRequest(url, {
            method: 'POST',
            body: JSON.stringify(filename)
        })
    }

    /**
     * Sends wakeword detected command
     * @param word
     */
    async sendCommandWakeWord (word: string) {
        const url = `${this.baseUrl}/command/${this.session}/command_wakeword`

        return this._sendRequest(url, {
            method: 'POST',
            body: JSON.stringify(word)
        })
    }

    /**
     * Invokes sendCommandAudio
     * @param filename
     */
    async sendCommandAudio (filename: string) {
        const url = `/kaia/command/${this.session}/command_audio`
        return this._sendRequest(url, {
            method: 'POST',
            body: JSON.stringify(filename)
        })
    }

    /**
     * Stops active audio recording
     */
    async stopRecording () {
        const formData = new FormData()
        formData.append('client_id', this.session)

        const url = `/audio_end`

        const response = await this._sendRequest(url, {
            method: 'POST',
            body: formData
        })
        console.log('Audio end response:', response)
        return response
    }

    async _sendRequest (url: string, options: RequestInit) {
        try {
            const defaultHeaders: Record<string, string> = {
                'Accept': 'application/json'
            }

            // Don't set Content-Type for FormData - browser will set it automatically with boundary
            if (!(options?.body instanceof FormData)) {
                defaultHeaders['Content-Type'] = 'application/json; charset=UTF-8'
            }

            const response = await fetch(url, {
                headers: defaultHeaders,
                ...options
            })

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`)
            }

            const contentType = response.headers.get('content-type')
            if (contentType === 'application/json') {
                return await response.json()
            }
            return await response.text()
        } catch (error) {
            console.error(`Error with request to ${url}:`, error)
            throw error
        }
    }
}