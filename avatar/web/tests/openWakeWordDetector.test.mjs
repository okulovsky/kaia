// Run after `npx vite build`: node --test tests/openWakeWordDetector.test.mjs
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { OpenWakeWordDetector } from '../frontend/scripts/open-wake-word-detector.js'
import { SilenceControllingWakeWordDetector } from '../frontend/scripts/kaia-frontend.js'

class FakeWorker {
    static latest
    messages = []
    terminated = false
    constructor () { FakeWorker.latest = this }
    postMessage (message) { this.messages.push(message) }
    terminate () { this.terminated = true }
    respond (message) { this.onmessage({ data: message }) }
}

globalThis.Worker = FakeWorker
globalThis.window = { location: { href: 'https://kaia.test/' } }

async function setup () {
    const events = []
    const detector = new OpenWakeWordDetector({ dispatcher: { push: event => events.push(event) } })
    const ready = detector.initialize()
    const worker = FakeWorker.latest
    worker.respond({ type: 'ready' })
    await ready
    return { detector, worker, events }
}

function frame (index) {
    return {
        sampleRate: 16000, micTimestamp: index * 32,
        buffer: Float32Array.from({ length: 512 }, (_, i) => index * 512 + i),
    }
}

test('loads local assets once and preserves samples across 512 -> 1280 framing', async () => {
    const { detector, worker } = await setup()
    await detector.initialize()
    assert.equal(worker.messages.length, 1)
    assert.equal(worker.messages[0].assetBaseUrl, 'https://kaia.test/frontend/scripts/openwakeword')
    for (let i = 0; i < 5; i++) detector.detect(frame(i))
    assert.equal(worker.messages.length, 2, 'only one inference may run at a time')
    const first = worker.messages[1]
    assert.deepEqual(first.chunk, Float32Array.from({ length: 1280 }, (_, i) => i))
    worker.respond({ type: 'result', generation: first.generation, keyword: null })
    assert.deepEqual(worker.messages[2].chunk, Float32Array.from({ length: 1280 }, (_, i) => i + 1280))
})

test('delivers Alexa to the automaton and dispatcher exactly once', async () => {
    const { detector, worker, events } = await setup()
    for (let i = 0; i < 3; i++) assert.equal(detector.detect(frame(i)), false)
    worker.respond({ type: 'result', generation: worker.messages[1].generation, keyword: 'alexa' })
    assert.equal(detector.detect(frame(3)), true)
    assert.equal(detector.detect(frame(4)), false)
    assert.equal(events.length, 1)
    assert.equal(events[0].payload.word, 'alexa')
})

test('a pause discards partial audio and stale in-flight detections', async () => {
    const { detector, worker, events } = await setup()
    for (let i = 0; i < 3; i++) detector.detect(frame(i))
    const oldGeneration = worker.messages[1].generation
    detector.detect(frame(100))
    worker.respond({ type: 'result', generation: oldGeneration, keyword: 'alexa' })
    assert.equal(detector.detect(frame(101)), false)
    detector.detect(frame(102))
    const next = worker.messages.at(-1)
    assert.notEqual(next.generation, oldGeneration)
    assert.equal(next.chunk[0], 100 * 512)
    assert.equal(events.length, 0)
})

test('slow inference has a bounded backlog and resets stale history', async () => {
    const { detector, worker } = await setup()
    const warn = console.warn
    console.warn = () => {}
    try {
        for (let i = 0; i < 200; i++) detector.detect(frame(i))
    } finally { console.warn = warn }
    const initial = worker.messages[1]
    worker.respond({ type: 'result', generation: initial.generation, keyword: 'alexa' })
    assert.ok(worker.messages.at(-1).generation > initial.generation)
    assert.equal(detector.detect(frame(200)), false)
})

test('rejects unsupported sample rates', async () => {
    const { detector } = await setup()
    assert.throws(() => detector.detect({ ...frame(0), sampleRate: 48000 }), /16000/)
})

test('silence gate stops OWW processing and resumes with a new audio generation', async () => {
    const { detector, worker, events } = await setup()
    const gate = new SilenceControllingWakeWordDetector({ detector, dispatcher: { subscribe () {} } })
    await gate.initialize()
    const processed = []
    let responseIndex = 1
    let detectOnNextResult = false
    let detections = 0
    const feed = (index, amplitude) => {
        const buffer = new Float32Array(512).fill(amplitude)
        if (gate.detect({ sampleRate: 16000, micTimestamp: index * 32,
            buffer, levelSum: 512 * Math.abs(amplitude) })) detections++
        while (responseIndex < worker.messages.length) {
            const request = worker.messages[responseIndex++]
            assert.equal(request.type, 'process')
            processed.push(request)
            worker.respond({ type: 'result', generation: request.generation,
                keyword: detectOnNextResult ? 'alexa' : null })
            detectOnNextResult = false
        }
    }

    for (let i = 0; i < 40; i++) feed(i, 0)
    assert.equal(processed.length, 0, 'quiet input must not reach the OWW worker')
    for (let i = 40; i < 60; i++) feed(i, 0.5)
    assert.ok(processed.length > 0, 'sound must activate OWW processing')
    const oldGeneration = processed.at(-1).generation
    for (let i = 60; i < 110; i++) feed(i, 0)
    const countAfterTail = processed.length
    for (let i = 110; i < 130; i++) feed(i, 0)
    assert.equal(processed.length, countAfterTail, 'processing must stop after the quiet tail')

    detectOnNextResult = true
    for (let i = 130; i < 150; i++) feed(i, 0.5)
    assert.ok(processed.length > countAfterTail)
    assert.ok(processed[countAfterTail].generation > oldGeneration,
        'resuming after filtered silence must reset the previous audio history')
    assert.equal(detections, 1)
    assert.equal(events.length, 1)
    assert.equal(events[0].payload.word, 'alexa')
})

test('model loading failures reject initialization and terminate the worker', async () => {
    const detector = new OpenWakeWordDetector({ dispatcher: { push () {} } })
    const ready = detector.initialize()
    const worker = FakeWorker.latest
    const error = console.error
    console.error = () => {}
    try { worker.respond({ type: 'error', message: 'Model not found' }) }
    finally { console.error = error }
    await assert.rejects(ready, /Model not found/)
    assert.equal(worker.terminated, true)
    assert.throws(() => detector.detect(frame(0)), /Model not found/)
})
