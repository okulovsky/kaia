// server-start-handler.ts
/**
 * A handler that listens for "/ServerStartEvent" messages
 * and reloads the current page.
 */
export class ServerStartedEventHandler {
    /**
     * @param dispatcher dispatches incoming Messages
     */
    constructor(dispatcher) {
        this.suffix = '/ServerStartedEvent';
        dispatcher.subscribe(this.suffix, this.handle.bind(this));
    }
    async handle(_msg) {
        window.location.reload();
    }
}
