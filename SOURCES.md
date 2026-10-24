# Implementation sources

- Portfolio theme: https://github.com/abbn7/glass-morphic-brilliance/blob/d1dab0ab8cf0e3f463c1a2faa7a8f21a06e94aa6/src/styles.css — exact dark tokens, gradients, glass borders/shadows, mobile blur values. Adapted at the repository owner's explicit request. No portfolio content, identity monogram, or WebGL scene copied.
- Local font: IBM Plex Sans Arabic, @fontsource package 5.2.7 — SIL Open Font License in static/fonts/OFL.txt.
- Agent Router Codex setup: https://agentrouter.org/docs/codex.html — custom provider, API key env variable, Responses API.
- Agent Router Claude Code setup: https://agentrouter.org/docs/claude-code.html — Anthropic route (documented, not used in this release).
- Agent Router Roo Code setup: https://agentrouter.org/docs/roocode.html — OpenAI-compatible /v1 route matching the user's screenshot.
- Official Codex: https://github.com/openai/codex — binary 0.163.0 from npm's official @openai/codex architecture package, npm SHA-512 verified during Docker build. Code mode host, voice components, Node.js and ripgrep are not installed because browser-model calls do not use them. Apache-2.0 license included.

## Workspace v2 redesign
The current runtime stylesheet is `static/workspace.css`. It retains the portfolio's layered-glass construction and local Arabic font, with a new user-requested AMOLED/ivory/champagne palette. The earlier teal/pink theme is no longer loaded. Chat, activity, proxy settings and desktop-browser framing are application-specific layouts.
