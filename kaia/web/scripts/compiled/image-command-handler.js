// image‐handler.ts
/**
 * A handler that listens for "/ImageCommand" messages
 * and writes the base64 payload directly into an <img>.
 */
export class ImageCommandHandler {
    /**
     * @param dispatcher dispatches incoming Messages
     * @param imgEl      the <img> element to update
     */
    constructor(dispatcher, imgEl) {
        this.imgEl = imgEl;
        this.suffix = '/ImageCommand';
        dispatcher.subscribe(this.suffix, this.handle.bind(this));
    }
    async handle(msg) {
        const fileId = msg.payload.file_id;
        const url = `/file-cache/download/${encodeURIComponent(fileId)}`;
        this.imgEl.src = url;
        return;
    }
}
