import { Dispatcher } from '../core/dispatcher.js'
import { Message, Envelop } from '../core/message.js'

export class FakeAudio {
    constructor({ dispatcher, autoconfirmationTimespanInSeconds = 0 }: { dispatcher: Dispatcher, autoconfirmationTimespanInSeconds?: number }) {
        const confirm = async (msg: Message) => {
            if (autoconfirmationTimespanInSeconds > 0) {
                await new Promise(resolve => setTimeout(resolve, autoconfirmationTimespanInSeconds * 1000))
            }
            dispatcher.push(
                new Message('SoundConfirmation', new Envelop(), { terminated: false })
                    .asConfirmationFor(msg)
            )
        }
        dispatcher.subscribe('SoundCommand', confirm)
        dispatcher.subscribe('SystemSoundCommand', confirm)
    }
}
