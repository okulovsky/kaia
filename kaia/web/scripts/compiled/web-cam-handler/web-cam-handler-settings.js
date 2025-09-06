export class WebCamHandlerSettings {
    constructor(init) {
        /** How often the picture is analyzed (framePerSecond cannot be less that 1, so if you need fewer analyses, use this) */
        this.pictureAnalysisIntervalMs = 1000;
        /** Frame width in pixels. */
        this.width = 320;
        /** Frame height in pixels. */
        this.height = 240;
        /**
         * Fraction of pixels (0..1) that must exceed per-pixel difference
         * to count as "motion".
         */
        this.threshold = 0.1;
        /**
         * Per-pixel average RGB difference (0..255) required
         * to mark a pixel as changed.
         */
        this.pixelThreshold = 30;
        /**
         * If true, handler will attempt to start the webcam automatically
         * when constructed (using getUserMedia) if videoElement has no stream.
         */
        this.shouldLaunchWebcam = true;
        Object.assign(this, init);
    }
}
