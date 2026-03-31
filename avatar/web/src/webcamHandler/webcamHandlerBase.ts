export type MovementEvent = {
  changedPixels: number;
  width: number;
  height: number;
  currentCanvas: HTMLCanvasElement;
  diffCanvas: HTMLCanvasElement;
};

export class WebcamHandlerBase {
  protected _onFrame?: (e: MovementEvent) => void

  public setOnFrame (cb?: (e: MovementEvent) => void) {
    this._onFrame = cb
  }
}