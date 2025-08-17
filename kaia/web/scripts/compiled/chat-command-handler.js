// chat-handler.ts
/**
 * A handler that listens for messages ending with '/ChatCommand'
 * and renders them into a chat container, plus enables
 * click‑and‑drag scrolling.
 */
export class ChatCommandHandler {
    /**
     * @param dispatcher  your Dispatcher instance
     * @param container   the HTML element (e.g. a <div>) to append chat <p>’s to
     * @param baseUrl     base URL to prepend to avatar paths
     */
    constructor(dispatcher, container, baseUrl) {
        this.container = container;
        this.baseUrl = baseUrl;
        this.suffix = '/ChatCommand';
        // subscribe to ChatCommand messages
        dispatcher.subscribe(this.suffix, this.handle.bind(this));
        // install click‑and‑drag scrolling
        let isDragging = false;
        let startScroll = 0;
        let startY = 0;
        this.container.addEventListener('mousedown', (e) => {
            isDragging = true;
            startScroll = this.container.scrollTop;
            startY = e.clientY;
            // prevent text selection while dragging
            e.preventDefault();
        });
        window.addEventListener('mouseup', () => {
            isDragging = false;
        });
        this.container.addEventListener('mousemove', (e) => {
            if (isDragging) {
                this.container.scrollTop = startScroll + (startY - e.clientY);
            }
        });
        this.container.addEventListener('mouseleave', () => {
            isDragging = false;
        });
    }
    async handle(msg) {
        const payload = msg.payload;
        const text = String(payload.text ?? '');
        const type = String(payload.type ?? 'to_user');
        const avatarId = payload.sender_avatar_file_id;
        const p = document.createElement('p');
        // alignment & styling
        switch (type) {
            case 'from_user':
                p.classList.add('right');
                break;
            case 'to_user':
                p.classList.add('left');
                break;
            case 'system':
                p.classList.add('system');
                break;
            case 'error':
                p.classList.add('error');
                break;
            default:
                p.classList.add('left');
        }
        if (avatarId && (type === 'from_user' || type === 'to_user')) {
            p.style.backgroundImage = `url('${this.baseUrl}${avatarId}')`;
        }
        // replace \n with <br>
        p.innerHTML = escapeHtml(text).split('\n').join('<br>');
        this.container.appendChild(p);
        this.container.scrollTop = this.container.scrollHeight;
    }
}
function escapeHtml(str) {
    return str.replace(/[&<>"']/g, c => {
        switch (c) {
            case '&': return '&amp;';
            case '<': return '&lt;';
            case '>': return '&gt;';
            case '"': return '&quot;';
            case "'": return '&#39;';
            default: return c;
        }
    });
}
