export class WebCamHandlerSettings {
  /** How often to sample the video (ms). */
  takePictureIntervalMs: number = 1000;

  /** Frame width in pixels. */
  width: number = 320;

  /** Frame height in pixels. */
  height: number = 240;

  /**
   * Fraction of pixels (0..1) that must exceed per-pixel difference
   * to count as "motion".
   */
  threshold: number = 0.1;

  /**
   * Per-pixel average RGB difference (0..255) required
   * to mark a pixel as changed.
   */
  pixelThreshold: number = 30;

  /**
   * If true, handler will attempt to start the webcam automatically
   * when constructed (using getUserMedia) if videoElement has no stream.
   */
  shouldLaunchWebcam: boolean = true;

  constructor(init?: Partial<WebCamHandlerSettings>) {
    Object.assign(this, init);
  }
}