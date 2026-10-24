# Validation report — 2026-10-24

## Passed

- Python compile and JavaScript syntax checks.
- 8 automated tests: owner authentication, CSRF/origin protection, private URL rejection, task persistence/recovery, API-key non-disclosure, exclusion of code/file tools, single-task cancellation, explicit approval gating, and file-scheme navigation rejection (some cases grouped in one test).
- Real Chromium + Browser-use integration with a deterministic model: successful completion, JPEG capture, Arabic text input, keyboard, click and scrolling.
- Docker image built successfully with pinned Python dependencies.
- Three sequential tasks submitted through the HTTP API, each completing two agent steps in a **512MiB / 1 CPU** container. Simultaneous second task rejected with 409.
- During 120 memory samples, highest observed working set: **338.4MiB**. No container OOM kill. This run used a deterministic test model, a simple public page, and live-view UI checks; it is not a benchmark for arbitrary websites or paid-model latency.
- Mobile browser automation at widths 360, 390 and 430 pixels: no horizontal overflow; no JavaScript page errors. Live frame width 390 pixels.
- Public HTTPS navigation through this environment's required proxy succeeded after importing its CA into Chromium's trust store. TLS verification stayed enabled.
- Production startup initializes a persistent volume then runs the serving process as UID 10001.

## Not passed / not established

- Historical direct-HTTP probes returned **401 unauthorized_client_error**. This was NOT proof of an invalid key. Official Codex CLI subsequently succeeded with the same key; see the update below.
- OpenRouter and Gemini account access remain untested. Agent Router inference and real browser-task completion are now verified through official Codex CLI.
- No deployment to a real Railway account. A local Docker resource limit approximates, but does not certify, Railway Free performance or monthly-credit longevity.
- No physical iPhone/Safari testing. Tests use Chromium with mobile dimensions; Safari-specific behavior must be checked after deployment.
- No 60-minute task endurance test, Google-account login, CAPTCHA solving, or broad-site compatibility test. CAPTCHA is a manual handoff, not automatic bypass.
- No promise that every page fits 512MB. Larger pages, screenshots, prompts, or long tasks may exceed it. Resource-pressure checks pause at step boundaries; they cannot prevent every sudden browser allocation.

## Sizes

- Static mobile UI assets approximately **96KB uncompressed**, including install icons. No model or Chromium binary is downloaded to the phone.
- Docker image approximately **1.24GB uncompressed** before minor documentation changes; includes Python dependencies and Chromium. This is disk/image size, not RAM usage.
- Source ZIP excludes the virtual environment, runtime data, browser profiles, secrets, caches, and all test session data.

## Differences from the earlier larger plan

This release intentionally has one small JavaScript/CSS frontend rather than React, no npm build, no desktop app, no terminal/code execution, no voice or skills loader, no precise monetary estimator, no adaptive high-frame-rate video, and no desktop-viewport toggle. It has a live mobile viewport, manual input, cancellation, recovery, approval gates, downloads, authentication, and a PWA manifest. It requires initial secret configuration; no public Railway template was published.

## Verified update — portfolio theme and official CLI transport

- Read portfolio CSS and shell source at commit `d1dab0ab8cf0e3f463c1a2faa7a8f21a06e94aa6`. Applied exact dark/glass tokens in `static/portfolio-theme.css`, including the original mobile blur reduction. Locally bundled Arabic fonts retain their OFL license.
- AgentRouter official docs specify Responses for Codex, and separate Anthropic/OpenAI-compatible paths.
- Same user-supplied key: official Codex CLI 0.163.0 returned **OK** with `gpt-5.6-sol`. Direct requests to both Responses and Chat Completions were denied as unauthorized client. No client-header spoofing was used.
- New CodexModel adapter: real structured-output probe succeeded, and real Browser-use + Chromium task completed through Agent Router with `gpt-5.6-sol`, returning the website purpose in Arabic (one agent step).
- `gpt-6.1-sol` also passed a real structured-output probe through the adapter.
- Automated test suite now has **10 passing tests**, including schema/secret isolation and terminating timed-out CLI processes.
- Earlier 338.4MiB memory result applies to the previous HTTP/mock-model build; it must not be treated as proof for the new CLI transport. The CLI binary adds approximately 297MB of uncompressed image storage, not a fixed amount of resident RAM.

## Final real-provider container test

- Image built with official Codex CLI 0.163.0 (npm SHA-512 integrity verified).
- Production application ran in Docker with **512MiB memory, no swap, and 1 CPU**.
- Real `gpt-6.1-sol` call through the CLI adapter completed an Arabic website-reading task via the HTTP task API in one agent step. Highest sampled container working set: **351.5MiB**. Test container and its injected key were removed after the test.
- This verifies the same supplied key works with the official CLI transport. It does not establish arbitrary-site compatibility or month-long Railway Free credit availability.
- Updated mobile UI smoke tests passed at 360/390/430px, with no JavaScript page errors or horizontal overflow. CSS inspection confirmed `oklch(0.08 0.01 260)` background and the exact portfolio strong-glass 18%/6% gradient.
- Updated static assets total **172,424 bytes (~168KiB)** uncompressed, including local fonts and icons. Docker image is approximately **1.54GB uncompressed** after adding the official CLI binary.
- Final source includes the requested portfolio-theme adaptation and CLI transport. No Railway account deployment or physical iPhone test was performed.
