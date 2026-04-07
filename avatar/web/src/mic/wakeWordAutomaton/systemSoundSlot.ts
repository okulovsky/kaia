import { Dispatcher } from '../../core/dispatcher.js'
import { Message, Envelop } from '../../core/message.js'

export class SystemSoundSlot {
    confirmed = false
    private commandId: string | null = null
    private soundName: string
    private dispatcher: Dispatcher

    constructor({ soundName, dispatcher }: { soundName: string, dispatcher: Dispatcher }) {
        this.soundName = soundName
        this.dispatcher = dispatcher
        dispatcher.subscribe('SoundConfirmation', async (msg) => {
            if (this.commandId !== null && msg.envelop.confirmation_for?.includes(this.commandId)) {
                this.confirmed = true
            }
        })
    }

    get isSent(): boolean {
        return this.commandId !== null
    }

    send(): void {
        if (this.isSent) throw new Error('SystemSoundSlot: already sent')
        const msg = new Message('SystemSoundCommand', new Envelop(), { sound_name: this.soundName })
        this.commandId = msg.envelop.id
        this.confirmed = false
        this.dispatcher.push(msg)
    }

    reset(): void {
        this.commandId = null
        this.confirmed = false
    }
}
