import { Message } from './message.js';
export class Dispatcher {
    constructor(client, updateRateInSeconds, busyElement) {
        this.handlers = new Map();
        this.running = false;
        this.client = client;
        this.rateMs = updateRateInSeconds * 1000;
        this.busyEl = busyElement;
        this.handledTypes = [];
        this.setBusy(false);
    }
    /** Subscribe a handler to any message whose type endsWith this suffix */
    subscribe(suffix, handler) {
        const list = this.handlers.get(suffix) ?? [];
        list.push(handler);
        this.handlers.set(suffix, list);
    }
    /** Start polling & dispatching */
    start() {
        if (this.running)
            return;
        this.running = true;
        this.handledTypes = [...this.handlers.keys()];
        void this.loop();
    }
    /** Stop polling */
    stop() {
        this.running = false;
        if (this.timeoutId != null) {
            window.clearTimeout(this.timeoutId);
            this.timeoutId = undefined;
        }
        this.setBusy(false);
    }
    /** Self-scheduling loop: strictly serial ticks */
    async loop() {
        while (this.running) {
            await this.tick();
            if (!this.running)
                break;
            await new Promise(resolve => {
                this.timeoutId = window.setTimeout(resolve, this.rateMs);
            });
        }
    }
    /**
     * Build and send frontend debug info for one polling round.
     * Must never throw — debug reporting must not break polling.
     */
    async sendFrontendDebugInfo(startedAt, finishedAt, msgs) {
        try {
            const fetchSeconds = (finishedAt - startedAt) / 1000;
            const messageTypes = Array.from(new Set(msgs.map(m => m.message_type)));
            const debugMsg = new Message("FrontendDebugInfo", undefined, {
                fetch_seconds: fetchSeconds,
                message_count: msgs.length,
                message_types: messageTypes,
                handled_types: Array.from(this.handledTypes),
                fetched_at: new Date().toISOString(),
            });
            //await this.client.addMessage(debugMsg);
        }
        catch (e) {
            console.warn("Dispatcher: failed to send FrontendDebugInfo", e);
        }
    }
    /** One polling round (network busy only during fetch; handlers awaited) */
    async tick() {
        let msgs;
        const startedAt = performance.now();
        try {
            this.setBusy(true);
            msgs = await this.client.getMessages(undefined, this.handledTypes);
            const finishedAt = performance.now();
            await this.sendFrontendDebugInfo(startedAt, finishedAt, msgs);
        }
        catch (e) {
            console.error('Dispatcher: fetch failed', e);
            return;
        }
        finally {
            this.setBusy(false);
        }
        const handlerPromises = [];
        for (const msg of msgs) {
            for (const [suffix, handlers] of this.handlers) {
                if (msg.message_type.endsWith(suffix)) {
                    for (const h of handlers) {
                        handlerPromises.push(h(msg, this.client).catch(err => console.error(`Handler for ${suffix} failed:`, err)));
                    }
                }
            }
        }
        if (handlerPromises.length > 0) {
            await Promise.allSettled(handlerPromises);
        }
    }
    setBusy(isBusy) {
        const el = this.busyEl;
        if (!el)
            return;
        el.hidden = !isBusy; // or: el.style.display = isBusy ? '' : 'none';
    }
}
