# Workspace v2 validation — 2026-10-24

## Functional checks

- **18 automated tests passed**: authentication/CSRF, private URL policy, persisted state, secret non-disclosure, excluded file/code tools, cancellation/single-task enforcement, explicit action approval, file-scheme blocking, CLI schema and process timeout, encrypted proxy storage, HTTP CONNECT authentication, SOCKS5 username/password and remote hostname handshake, SOCKS4a remote hostname/user ID, verified HTTPS proxy TLS, no direct retry when a proxy fails, message editing with interruption/history, starting chat without a link, and action events without logging typed values. Related cases are grouped into individual tests.
- Chromium + Browser-use integration passed: completion, JPEG snapshot, Arabic text input, key events, scrolling and clicking.
- Real Chromium through an authenticated local test HTTP proxy passed, forwarding through the environment's required egress proxy. Observed 9 target tunnel connections and a **1280×800** screenshot. No real residential-proxy account was supplied or tested.
- Mobile UI checks passed at **360, 390, 430px** and desktop **1280px**: no horizontal root overflow, composer inside the viewport, no JavaScript page errors. Live image measured **1280×800**. Zoom, activity drawer and saving masked proxy settings exercised.
- Real Agent Router `gpt-6.1-sol` task through the deployed app HTTP API completed, followed by a second user message and successful assistant reply. Conversation contained 6 messages and execution history contained 19 events. The edit control opened correctly in the real UI. Full edit/cancellation semantics are additionally covered by automated tests.

## Runtime measurement

The v2 runtime was exercised in Docker with **512MiB, no swap, and 1 CPU**, using the existing pinned-dependency image rebuilt with v2 application files. Highest sampled working set during the initial real task: **357.6MiB**. Follow-up execution succeeded but its peak was not separately sampled. The test image uses the same dependencies and runtime entrypoint as the supplied Dockerfile; dependency installation was verified in previous image builds.

This is a simple website test, not a general guarantee for heavy sites, 60-minute endurance, or Railway Free's monthly credit. The new desktop resolution can consume more memory on complex websites. A new Railway deployment and physical iPhone/Safari verification were not performed.

## What is exposed in the UI

The execution feed contains actual lifecycle and tool events, not hidden model reasoning. Failed attempts are labeled as failed attempts rather than completed steps. User-entered browser text is not logged. Owner message edits preserve prior replies as historical and do not undo external actions already performed.

## Proxy coverage and limits

Configured upstream schemes: HTTP, HTTPS, SOCKS5/SOCKS5h and SOCKS4a (SOCKS4 is handled using remote-DNS SOCKS4a). HTTP(S) supports Basic proxy credentials; SOCKS5 supports its standard username/password method; SOCKS4a accepts a user ID without password auth. Unsupported methods/certificates fail rather than silently connecting directly.

When enabled, browser traffic goes through the local gateway and chosen upstream; origin hostnames are passed to the upstream without local origin DNS lookup. Chromium QUIC, DNS prefetch and non-proxied WebRTC UDP are restricted by launch flags. A packet-level, OS-wide DNS/WebRTC leak audit was not performed. Model API traffic is separate, so this is not a full-system VPN or a promise of anonymity or CAPTCHA avoidance. Browser cookies, account identity and browser fingerprint remain relevant. Upstream-resolved DNS and the remote proxy's internal-network policy are controlled by that provider.

Proxy credentials are encrypted at rest with Fernet; only a masked configuration is returned. The encryption key defaults to a 0600 file on the same persistent volume, so this does not protect against an administrator who can read the whole host/volume.

## Artifacts

- `preview-mobile.png`: real v2 mobile interface after a real model task and follow-up.
- `preview-activity.png`: real task activity drawer.
- `README.md` and `QUICKSTART_AR.md`: deployment, chat controls, proxy setup and limits.
- Source archive excludes runtime data, profiles, environment files, provider keys and virtual environments.

Earlier results in `VALIDATION.md` are historical. This report describes the current v2 behavior.
