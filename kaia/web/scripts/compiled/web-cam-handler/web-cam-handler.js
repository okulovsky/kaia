import { WebCamHandlerSettings } from './web-cam-handler-settings.js';
import { Message } from '../message.js';
export class WebCamHandler {
    setOnFrame(cb) {
        this._onFrame = cb;
    }
    constructor(client, baseUrl) {
        this.settings = new WebCamHandlerSettings();
        this.client = client;
        this.baseUrl = baseUrl;
        this.videoElement = document.createElement('video');
        const _currentCanvas = document.createElement('canvas');
        _currentCanvas.width = this.settings.width;
        _currentCanvas.height = this.settings.height;
        this._currentCanvas = _currentCanvas;
        const _diffCanvas = document.createElement('canvas');
        _diffCanvas.width = this.settings.width;
        _diffCanvas.height = this.settings.height;
        this._diffCanvas = _diffCanvas;
        // This library can launch webcam automatically if the video element is not provided
        if (this.settings.shouldLaunchWebcam === true) {
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                navigator.mediaDevices
                    .getUserMedia({ video: true, audio: false })
                    .then((stream) => {
                    this.videoElement.srcObject = stream;
                    this.videoElement.play();
                })
                    .catch((err) => {
                    console.error(`An error occurred while accessing webcam: ${err}`);
                });
            }
            else {
                console.error("MediaDevices API not available in this environment.");
            }
        }
        this._isStreaming = false;
    }
    start() {
        const video = this.videoElement;
        video.addEventListener('canplay', (_ev) => {
            if (!this._isStreaming) {
                this._isStreaming = true;
                if (this.settings.takePictureIntervalMs > 0) {
                    setInterval(() => this.takeNextPictureAndDetectMovement(), this.settings.takePictureIntervalMs);
                }
            }
        });
    }
    takeNextPictureAndDetectMovement() {
        // stashing current image in the diff and getting data
        const diffContext = this._diffCanvas.getContext('2d');
        diffContext.clearRect(0, 0, this._diffCanvas.width, this._diffCanvas.height);
        diffContext.drawImage(this._currentCanvas, 0, 0);
        const img1Data = diffContext.getImageData(0, 0, this.settings.width, this.settings.height).data;
        // Take new screenshot
        const currentContext = this._currentCanvas.getContext('2d');
        currentContext.drawImage(this.videoElement, 0, 0, this.settings.width, this.settings.height);
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
            const url = `${this.baseUrl}/file-cache/upload/${fileName}`;
            this._currentCanvas.toBlob((blob) => {
                if (!blob)
                    return;
                const form = new FormData();
                form.append('content', blob, `${fileName}.png`); // поле 'content', как в requests files=
                fetch(url, {
                    method: 'POST',
                    body: form, // multipart/form-data (заголовок ставит браузер)
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
