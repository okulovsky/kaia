## Interface

```ts
interface ILoadingScreenComponent {
    initialize(): Promise<void>  // resolves = ready, rejects with error message string
}
```

`LoadingScreen` derives the display name from `component.constructor.name` — no `name` property needed on implementing classes.

## LoadingScreen

`LoadingScreen` accepts: a div element, a list of `ILoadingScreenComponent`, and a callback.

On construction it makes the div visible and renders one row per component showing `"<name>: loading"`.

For each component it calls `initialize()` and attaches per-promise handlers:
- On resolve: update that component's row to `"<name>: ready"`
- On reject: update that component's row to show the error message

After every resolve/reject it checks whether all components have reported success. If yes, it hides the div and fires the callback. (If any component errored, the callback is never fired and the screen stays visible with the error.)

Do NOT use `Promise.all` — attach `.then`/`.catch` per component so the UI updates incrementally.

## WakeWordDetector

Implements `ILoadingScreenComponent`:
- `name` = `"Wake word detector"` (or similar)
- `initialize()` exposes the existing private `_initialize()` as a public Promise — make `_initialize` public (or add a thin wrapper). The lazy-init guard (`initializing` flag) should be replaced: `LoadingScreen` is now the sole caller of `initialize()`.

## Files to update

### avatar/web/src/loadingScreen/
Create two new files:
- `iLoadingScreenComponent.ts` — the interface
- `loadingScreen.ts` — the `LoadingScreen` class

### avatar/web/src/mic/wake_word_automaton/wakeWordDetector.ts
- Expose `initialize(): Promise<void>` (replaces `_initialize`)
- Remove the lazy-init logic from `detectWakeWord` (it no longer needs to trigger init)

### avatar/tests/test_web/test_mic/test_wake_word.py and test_automaton.py
Replace the `window.voskReady` polling pattern with `LoadingScreen`:
- In the inline HTML, construct a `LoadingScreen` with the wake word detector
- The callback should: send `InitializationEvent` to the dispatcher, then call `controller.start()`
- In the Python test, replace `WebDriverWait(env.driver, 120).until(lambda d: d.execute_script('return window.voskReady === true'))` with `reader.query(120).where(lambda z: isinstance(z, InitializationEvent)).first()`

### kaia/web/index.html
Replace the manual polling block with `LoadingScreen`:
- Construct `LoadingScreen` with `[wake]` and a callback that sends `InitializationEvent` and calls `controller.start()`
- Remove the `wakeReady` Promise.race block
- `await controller.start()` moves into the callback (no longer called at top level)
