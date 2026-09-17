# v0.1.0 repository preparation / 第一阶段验收

Scope: stage one of [the three-stage plan](../SessionGlow_三阶段发布计划.md). No community announcements, Soft Launch campaigns or broad promotion are included.

## Positioning

Use **Ambient status lights for your OpenCode agents.** in the English README, About and release materials. Chinese: **让每个 OpenCode 会话，都有一盏状态灯。** SessionGlow observes work; it is not a session manager or agent orchestrator.

## Local deliverables

- [x] MIT `LICENSE`, copyright 2026 YidaHao; dependency licenses remain separate.
- [x] English `README.md`, Chinese `README.zh-CN.md`, language links and legacy English redirect.
- [x] First viewport: positioning, 12-second demo and four states; compatibility matrices and package-first Quick Start.
- [x] Actual-renderer GIF/WebM showing work, attention, simulated approval, resumed work and completion.
- [x] `docs/assets/social-preview.png`, 1280 × 640, plus reproducible media script.
- [x] Deterministic `sessionglow_0.1.0_amd64.deb` and `SHA256SUMS` build.
- [x] Per-user plugin registration, safe migration/removal and explicit upgrade/uninstall instructions.
- [x] `CONTRIBUTING.md`, bilingual issue forms and three scoped roadmap descriptions.
- [x] CI tests, lint, package install/reinstall/removal, and tagged-release publication workflow.
- [ ] Remote CI passing, roadmap issues created and release assets verified (fill in after publication).

AppImage is a **deferred recommendation**, not a v0.1.0 asset. The roadmap issue specifies portable runtime, licensing and plugin lifecycle acceptance criteria. Wayland/KDE remain untested, not “testing” or “supported”.

## GitHub metadata requiring owner access

Git SSH permission is sufficient to push commits/tags, but does not authenticate GitHub CLI or grant repository-settings API access. With `gh` authenticated as the owner, run:

```bash
gh repo edit YidaHao/SessionGlow \
  --description 'Ambient status lights for your OpenCode agents.' \
  --add-topic opencode --add-topic ai-agent --add-topic coding-agent \
  --add-topic developer-tools --add-topic agent-monitoring \
  --add-topic linux --add-topic desktop-widget --add-topic pyqt
```

Then upload `docs/assets/social-preview.png` via repository **Settings → General → Social preview**. This is a browser-only repository setting; adding the PNG to Git does not activate it.

- [ ] About updated online.
- [ ] Topics verified online.
- [ ] Social Preview uploaded and verified online.

## Publication

CI runs on `main`, PRs and tags. A matching `v0.1.0` tag triggers tests, builds the package, checks it inside an isolated Ubuntu 22.04 container, then publishes the tested package and checksums with `gh release create`. The workflow's scoped `GITHUB_TOKEN` can create releases/issues; it cannot change administrative repository settings.

The first tagged release creates three actionable roadmap issues using `scripts/publish_roadmap.py`: Wayland/KDE validation, AppImage packaging and English UI. They are not speculative feature promises.

Release notes: [v0.1.0](releases/v0.1.0.md). Track online verification below; leave items open until they are actually checked.
