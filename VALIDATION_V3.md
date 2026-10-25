# Minimal v3 validation — 2026-10-24

## Interface and interaction

- Browser image starts at x=0 and spans the full viewport at 360, 390, 430 and 1280px. No horizontal document overflow; the composer remains inside the viewport.
- Native browser uses desktop width 1280, DPR 1 and height 800–2200; containers limited to 600MiB or less cap it at 1600. The image preserves its actual aspect ratio. At 390×844 the 1280×1600 small-container frame occupies 390×487.5px. The taller 1280×2200 capture on a larger environment occupies 390×670.3px. Both start below the 42px header.
- Real CDP click mapping verified at fit and 150% zoom: a known native target received exactly two clicks. Native `innerWidth` and `screen.width` both measured 1280.
- UI regression passed for retained message elements, message edit controls, on-demand event dialog, masked proxy save and the composer switching between send and pause. No JavaScript page errors.
- A clearly synthetic timeline fixture verifies that the elapsed counter updates without adding fabricated events or rebuilding old message elements. This fixture is not model inference.

## Application checks

**25 automated tests passed** covering authentication/CSRF, public URL policy, persistent state, secret non-disclosure, tool restrictions, single-task/cancellation, mutation approval, official CLI transport/schema/timeout, encrypted proxy configuration, supported proxy handshakes and fail-closed behavior, message editing, real action event metadata, bounded/deferred desktop layout, small-container capture limits, browser startup readiness and read-only tool approval classification.

The read-only Browser-use tools `find_elements`, `search_page` and `dropdown_options` now run without a mutation approval. Clicking, typing and other mutating actions retain their approval gate. Their user-facing activity labels are Arabic.

Chromium + Browser-use integration completed with a deterministic test model while live snapshots were running. It executed a real `find_elements` read without a mutation approval, then completed on the second model call, with ten live frames observed. The model received actual DOM state and a screenshot at 1280×2200. JPEG output, Arabic text input, key events, scrolling and clicking passed. This test is separate from the real provider check below.

Real Chromium through an authenticated local HTTP proxy passed this revision's checks, forwarding through the environment's required egress proxy. The direct proxy engine test produced a 1280×800 frame and seven target tunnels. No residential-proxy account or OS-wide packet leak audit was performed.

## Real model and container

Agent Router `gpt-6.1-sol` through the official Codex transport completed a real documentation-page task started through the actual UI, with live streaming open. It returned **OpenAI Agents SDK**. The final run completed in **22.4 seconds**, with one agent step, two conversation messages and nine real events. No UI page errors occurred. A separate earlier live task correctly returned the permitted usage of example.com in Arabic.

The container was limited to **512MiB, no swap and 1 CPU**. The final 1280×1600 run peaked at a sampled **369.3MiB**, recorded **zero OOM kills**, delivered **23 live frames**, and delivered **four additional frames after completion**. The browser remained usable after the answer. The runtime uses the previously built pinned dependency layer with the latest v3 application files. These measurements are not a guarantee for complex sites or long-duration tasks.

During development, a taller 2200px capture on the documentation site hit the container memory limit after the answer completed. This was a real browser OOM, despite the successful model result. That configuration is not used on 512MiB now: the native capture is capped at 1600px, and the frontend waits for layout adjustment before starting a task. Another earlier run experienced model latency and screenshot errors, then waited on a read-only tool misclassified for approval. Read-only approval, browser startup readiness and model timeout alignment were corrected and covered by tests. These changes do not claim all Chromium or provider failures are eliminated.

No new Railway deployment, physical iPhone/Safari session or hour-long endurance run was performed. Railway's monthly free credit and persistence requirements remain as documented in README.md.

## Delivered artifacts

- `preview-mobile.png`: actual minimal mobile interface with the real completed task, after manually reopening the same documentation page.
- `preview-running.png`: actual live task interface.
- `preview-activity.png`: actual execution history, opened on demand.
- Dockerfile, Railway configuration, local Compose setup and Arabic quick start are included.
- Source archive excludes provider keys, runtime profiles, cookies, databases, environment secrets and virtual environments. Test fixture routes are excluded from Docker and never imported by production.

`VALIDATION.md` and `VALIDATION_V2.md` describe historical versions.
