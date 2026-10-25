# Implementation sources

- Portfolio theme: https://github.com/abbn7/glass-morphic-brilliance/blob/d1dab0ab8cf0e3f463c1a2faa7a8f21a06e94aa6/src/styles.css — exact dark tokens, gradients, glass borders/shadows, mobile blur values. Adapted at the repository owner's explicit request. No portfolio content, identity monogram, or WebGL scene copied.
- Local font: IBM Plex Sans Arabic, @fontsource package 5.2.7 — SIL Open Font License in static/fonts/OFL.txt.
- Agent Router Codex setup: https://agentrouter.org/docs/codex.html — custom provider, API key env variable, Responses API.
- Agent Router Claude Code setup: https://agentrouter.org/docs/claude-code.html — Anthropic route (documented, not used in this release).
- Agent Router Roo Code setup: https://agentrouter.org/docs/roocode.html — OpenAI-compatible /v1 route matching the user's screenshot.
- Official Codex: https://github.com/openai/codex — binary 0.163.0 from npm's official @openai/codex architecture package, npm SHA-512 verified during Docker build. Code mode host, voice components, Node.js and ripgrep are not installed because browser-model calls do not use them. Apache-2.0 license included.

## Minimal v3 redesign

The user's latest screenshots are the visual source for this revision: black AMOLED canvas (`#000000`), warm ivory (`#e8e2d4`), charcoal (`#302c27`) and restrained terracotta (`#ce785e`). The runtime stylesheet is `static/workspace.css`. It adapts the portfolio's glass borders, inner highlights and local Arabic type to a much thinner interface. The previous teal/pink and champagne card layouts are no longer loaded.

The full-width desktop browser, floating chat, compact domain field, icon-only tools and small live activity line are specific to this application. No text, illustration, identity or chart was copied from the reference images. Icons are inline SVG paths; animations use CSS and the Web Animations API, without an animation library or decorative continuous rendering loop.
