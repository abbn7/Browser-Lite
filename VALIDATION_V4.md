# v4 validation — 2026-10-25

- 29 automated tests passed, including encrypted model profiles, environment fallback, persistence after reopening storage, masked responses, credential-safe validation errors, busy-task guards, and a structured-output + vision draft probe with a mocked provider. Existing authentication, proxy, tool approval, CLI transport and conversation checks passed.
- Chromium UI passed at 360, 390, 430 and 1280px: no horizontal document overflow; real CDP click target hit at fit and zoom; retained keyed message nodes; actual elapsed timer without fabricated events; send/pause and editing; masked proxy save.
- New UI checks saved a test model profile, reopened settings without exposing its key, and deleted it. Keys used in tests are fixtures, not real provider credentials.
- Keyboard geometry simulation kept browser pane height unchanged, composer within the reduced visual viewport, draft intact, and emitted no browser-layout request. This is desktop Chromium simulation, not physical iPhone/Safari verification.
- Real Browser-use/Chromium integration received DOM + vision while live frames ran, executed a read-only find-elements operation, and completed on its second deterministic model call. Unicode input, key, click and scroll checks passed.
- Current build reuses the pinned dependency image, with v4 source copied into it. No UI runtime or Python dependency was added.

No new real NVIDIA/OpenRouter/Google credentials were supplied or used for this revision. Their transports are implemented and probes are available; universal model compatibility and free service access are not claimed. Historical Agent Router real-model results remain in VALIDATION_V3.md. No new Railway deployment or hour-long endurance test was performed.

Preview images show the real documentation website and a synthetic conversation/activity fixture to illustrate the UI. preview-keyboard.png simulates a reduced visual viewport; it does not contain a real iOS keyboard. Reduced motion disables decorative animations.

Docker verification with 512MiB/no swap/one CPU passed: two deterministic model calls, actual DOM and vision, five live frames, Arabic input/click/scroll, and zero OOM kills. Highest sampled working set was 460.8MiB with the idle API process plus a separate test engine process running together. This is not a new paid-provider benchmark or a guarantee for heavy sites. The test process used UID 10001 and the environment's trusted proxy CA, matching the runtime trust store.
