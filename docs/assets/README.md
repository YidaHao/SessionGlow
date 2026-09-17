# 首页动效素材

素材由 SessionGlow 本身离屏绘制，使用程序内置的中文演示会话，不包含真实用户桌面或聊天内容。

| 文件 | 用途 |
| --- | --- |
| `sessionglow-demo.gif` | README 内直接播放的动效，420 × 580，12 fps，20 秒循环 |
| `sessionglow-demo.webm` | 高清演示，420 × 580，24 fps，20 秒 |

四根灯管分别展示运行、失败、完成和待确认；第五根每 5 秒切换一次状态。

## 重新生成

需要系统 PyQt5 和 ffmpeg。在仓库根目录运行：

```bash
PYTHONPATH=. /usr/bin/python3 tests/render_demo.py docs/assets/sessionglow-demo.webm

ffmpeg -y -i docs/assets/sessionglow-demo.webm \
  -filter_complex '[0:v]fps=12,split[frames][colors];[colors]palettegen=max_colors=128:stats_mode=diff[palette];[frames][palette]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle' \
  -loop 0 docs/assets/sessionglow-demo.gif
```

GIF 用于 GitHub README 内嵌播放，WebM 保留更高帧率。重新生成后同时检查四种稳定状态和第五根灯管的过渡。
