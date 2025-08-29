// Панель, которая подписывается на detector.onFrame и рисует два <img> в переданном div.
export class WebCamHandlerDebugger {
    constructor(detector) {
        this._active = false;
        this._onFrame = (e) => {
            if (!this._active)
                return;
            if (this._imgCurrent)
                this._imgCurrent.src = e.currentCanvas.toDataURL('image/png');
            if (this._imgDiff) {
                if (e.diffCanvas)
                    this._imgDiff.src = e.diffCanvas.toDataURL('image/png');
                else
                    this._imgDiff.removeAttribute('src');
            }
        };
        this.detector = detector;
        this._imgCurrent = document.createElement('img');
        this._imgCurrent.style.maxWidth = '50%';
        this._imgDiff = document.createElement('img');
        this._imgDiff.style.maxWidth = '50%';
    }
    setPanel(panel) {
        this.panel = panel;
    }
    start() {
        if (!this.panel) {
            throw new Error("Panel not initialized");
        }
        // сделать div видимым
        const cs = getComputedStyle(this.panel);
        if (cs.display === 'none')
            this.panel.style.display = 'block';
        if (cs.visibility === 'hidden')
            this.panel.style.visibility = 'visible';
        // создать картинки при первом запуске
        this.panel.appendChild(this._imgCurrent);
        this.panel.appendChild(this._imgDiff);
        this.detector.setOnFrame(this._onFrame);
        this._active = true;
        // следим за видимостью
        this._observer?.disconnect();
        this._observer = new MutationObserver(() => this._checkVisibility());
        this._observer.observe(this.panel, {
            attributes: true,
            attributeFilter: ['style', 'class', 'hidden'],
        });
        this._checkVisibility(); // вдруг скрыт прямо сейчас
    }
    _checkVisibility() {
        if (!this.panel) {
            return;
        }
        const cs = getComputedStyle(this.panel);
        const hidden = cs.display === 'none' || cs.visibility === 'hidden' || !this.panel.isConnected;
        if (hidden) {
            this.detector.setOnFrame(undefined); // отписка
            this._observer?.disconnect();
            this._observer = undefined;
            this._active = false;
        }
    }
}
