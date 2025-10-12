import { WebCamHandlerSettings } from './web-cam-handler-settings.js';
import { Message } from '../message.js';
import { WebCamHandlerBase } from './web-cam-handler-base.js';
export class WebCamHandlerSnapshot extends WebCamHandlerBase {
    constructor(client, baseUrl) {
        super();
        this.settings = new WebCamHandlerSettings();
        this.client = client;
        this.baseUrl = baseUrl;
        const _currentCanvas = document.createElement('canvas');
        _currentCanvas.width = this.settings.width;
        _currentCanvas.height = this.settings.height;
        this._currentCanvas = _currentCanvas;
        const _diffCanvas = document.createElement('canvas');
        _diffCanvas.width = this.settings.width;
        _diffCanvas.height = this.settings.height;
        this._diffCanvas = _diffCanvas;
        this._isStreaming = false;
    }
    start() {
        if (this._isStreaming)
            return;
        this._isStreaming = true;
        const delay = this.settings.pictureAnalysisIntervalMs;
        const run = async () => {
            try {
                await this.takeNextPictureAndDetectMovement();
            }
            catch (e) {
                console.error(e);
            }
            finally {
                if (!this._isStreaming)
                    return;
                window.setTimeout(run, delay);
            }
        };
        run();
    }
    /** Делает один снимок в target-канвас и сразу освобождает камеру */
    async _getPicture(target) {
        const w = this.settings.width;
        const h = this.settings.height;
        // не просим fps вообще — берём первый доступный кадр
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { width: { ideal: w }, height: { ideal: h } },
            audio: false,
        });
        try {
            const v = document.createElement('video');
            v.autoplay = true;
            v.muted = true;
            v.playsInline = true;
            v.srcObject = stream;
            // ждём первый кадр
            if (v.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) {
                await new Promise((res) => v.addEventListener('loadeddata', () => res(), { once: true }));
            }
            // рисуем в канвас нужного размера
            target.width = w;
            target.height = h;
            const ctx = target.getContext('2d', { willReadFrequently: true });
            target.getContext('2d').drawImage(v, 0, 0, w, h);
        }
        finally {
            // обязательно выключаем камеру
            stream.getTracks().forEach((t) => t.stop());
        }
    }
    async takeNextPictureAndDetectMovement() {
        const diffContext = this._diffCanvas.getContext('2d');
        diffContext.clearRect(0, 0, this._diffCanvas.width, this._diffCanvas.height);
        diffContext.drawImage(this._currentCanvas, 0, 0);
        const img1Data = diffContext.getImageData(0, 0, this.settings.width, this.settings.height).data;
        // Take new screenshot
        const currentContext = this._currentCanvas.getContext('2d');
        await this._getPicture(this._currentCanvas);
        const img2Data = currentContext.getImageData(0, 0, this.settings.width, this.settings.height).data;
        // Preparing diffData
        diffContext.clearRect(0, 0, this.settings.width, this.settings.height);
        const diffImageData = diffContext.createImageData(this.settings.width, this.settings.height);
        let changedPixels = 0;
        for (let i = 0; i < img1Data.length; i += 4) {
            const rDiff = Math.abs(img1Data[i] - img2Data[i]);
            const gDiff = Math.abs(img1Data[i + 1] - img2Data[i + 1]);
            const bDiff = Math.abs(img1Data[i + 2] - img2Data[i + 2]);
            if ((rDiff + gDiff + bDiff) / 3 > this.settings.pixelThreshold) {
                changedPixels++;
                diffImageData.data[i] = 255;
                diffImageData.data[i + 1] = 0;
                diffImageData.data[i + 2] = 0;
                diffImageData.data[i + 3] = 255;
            }
            else {
                diffImageData.data[i] = 0;
                diffImageData.data[i + 1] = 0;
                diffImageData.data[i + 2] = 0;
                diffImageData.data[i + 3] = 255;
            }
        }
        diffContext.putImageData(diffImageData, 0, 0);
        this._onFrame?.({
            changedPixels,
            width: this.settings.width,
            height: this.settings.height,
            currentCanvas: this._currentCanvas,
            diffCanvas: this._diffCanvas,
        });
        if (changedPixels > this.settings.threshold * this.settings.width * this.settings.height) {
            const fileName = `webcam_${crypto.randomUUID()}.png`;
            const url = `${this.baseUrl}/file-cache/file/${fileName}`;
            this._currentCanvas.toBlob((blob) => {
                if (!blob)
                    return;
                fetch(url, {
                    method: 'PUT',
                    body: blob, // multipart/form-data (заголовок ставит браузер)
                })
                    .then(async (res) => {
                    if (!res.ok)
                        throw new Error(await res.text());
                    const eventMsg = new Message('ImageEvent');
                    eventMsg.payload = { file_id: fileName };
                    this.client.addMessage(eventMsg);
                })
                    .catch((err) => console.error('upload failed:', err));
            }, 'image/png');
        }
    }
}
