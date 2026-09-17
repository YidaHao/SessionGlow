# Release media / 发布素材

The landing-page media uses SessionGlow's actual tube renderer with synthetic English session titles. No user desktop, conversation or project information is captured. English media labels are presentation text; v0.1.0's normal UI is still Chinese.

| File | Purpose |
| --- | --- |
| `sessionglow-demo.gif` | 12-second looping README demo, 420 × 488, 12 fps |
| `sessionglow-demo.webm` | Same scenario at 24 fps |
| `social-preview.png` | 1280 × 640 GitHub Social Preview image |

The first row runs, requests permission, shows a simulated “Approved” caption, resumes and completes. Other rows show parallel work, completion and failure. SessionGlow does not approve permissions; this is a staged illustration of the lifecycle.

中文：首行依次演示运行、等待授权、模拟用户批准、恢复运行和完成，其余行显示并行任务与不同结果。素材不含真实聊天或桌面内容。

## Regenerate

Install system PyQt5 and ffmpeg, then run at the repository root:

```bash
/usr/bin/python3 scripts/render_release_media.py
```

The longer original demo is still available through `./run.sh --demo` and `tests/render_demo.py`.

## Set the Social Preview

In GitHub: repository **Settings → General → Social preview → Edit → Upload an image**. Select `social-preview.png`. GitHub currently requires a browser upload for this setting; committing the file does not activate it automatically.

See [release checklist](../RELEASE_CHECKLIST.md) for the repository description, topics and verification status.
