# SessionGlow

把 OpenCode 的会话状态放进一个安静的悬浮面板。每个主会话对应一根灯管，所有光效限制在面板内部。

完整指南：[安装与 OpenCode / OpenChamber 接入](docs/INSTALL.md) · [日常使用、设置与问题排查](docs/USAGE.md)。

针对 Ubuntu 22.04.5 / GNOME 42.9 / X11 制作，使用系统 Python 3.10 + PyQt5。Python 后端和 OpenCode 插件均无其它第三方依赖。原 WindowRag Ubuntu 实现已单独保存在 `WindowRag` 仓库的 `feat/ubuntu-x11` 分支，提交 `d59bfb3`。

## 打开、隐藏、退出

```bash
./run.sh
```

也可以在 Ubuntu 应用菜单搜索 **SessionGlow**（先运行下面的安装命令）。面板标题栏可拖动；右上角 `−` 隐藏到托盘，`···` 打开菜单。托盘支持显示/隐藏、置顶、数量、外观设置和退出；终端运行时也可以 Ctrl+C 退出。

本机已安装 PyQt5，其他 Ubuntu 机器可执行 `sudo apt install python3-pyqt5`。

预览四种状态与连续切换，不需要 OpenCode：

```bash
./run.sh --demo
```

演示模式用明确标注的合成数据，不接收真实会话、不写配置或会话历史；第五根灯管每 5 秒切换一次状态。

## 灯管状态

| 状态 | 颜色 | 效果 |
| --- | --- | --- |
| 进行中 | 蓝色 | 五股加粗电流舒缓交叉流动，粒子沿电流和空腔漂浮 |
| 任务失败 | 红色 | 收敛为近乎水平的电流，粒子停住，仅有细微抖动 |
| 已完成 | 绿色 | 电流与粒子消失，管腔充满缓慢流动的绿色液体 |
| 待确认 | 黄色 | 五股加粗交叉电流与空腔粒子，与蓝色近似的波幅，加上更不规则的快速抖动 |

所有状态变化经过 0.8 秒平滑过渡，粒子位置与动画相位保持连续，中途切换从当前画面继续。绿色的内部光带表现液体折射，不是电流或粒子。

蓝色和黄色状态各有 19 颗沿电流运动的粒子，以及 38 颗在管腔内独立漂浮的细小粒子。转为失败时，附加电流和空腔粒子逐渐淡出，沿线粒子回到主电流并停止；转为完成时一起渐隐为绿色液体。

没有可靠任务结果时使用灰色待机灯。连接丢失时灯管变暗并标明“连接中断 · 上次状态”，保留上次的任务状态；不会将断线当作完成。用户主动取消任务显示红色并标明“已取消”；普通工具失败后继续执行或重试仍显示蓝色。

## OpenCode 接入

安装全局插件入口和应用启动项：

```bash
/usr/bin/python3 install.py
```

从本机之前的 WindowRag 接入切换：

```bash
/usr/bin/python3 install.py --replace-windowrag
```

安装器会把旧的 `~/.config/opencode/plugins/windowrag.js` 保存为 `.js.disabled`，写入新的 `sessionglow.js`。它不改写 `opencode.json`，也不会修改其它插件。入口引用本仓库文件，移动仓库后应更新入口路径。

**安装或更新插件后，退出并重启 OpenCode。** 在原来的项目目录执行 `opencode -c` 可继续最近的会话；使用独立 `opencode serve` 的客户端，需要重启对应服务。SessionGlow 本身可以一直开着。

插件使用实际 `session.status`、`session.error`、授权/提问和消息元数据事件。程序没有 CPU 兜底，不凭进程负载推测任务。只传输会话 ID、父子关系、标题、项目目录、状态和时间，不传输提示词、回答正文或工具参数。

面板底部显示连接数量。插件每 5 秒发送当前快照，面板关闭不阻塞 OpenCode；重新打开面板后会自动恢复连接。20 秒没有心跳时标记断线。

默认端口 `127.0.0.1:8790`，仅监听本机：

```bash
curl -s http://127.0.0.1:8790/health
```

接口显示连接数、当前显示的会话和状态。自定义端口时两端必须一致：`./run.sh --port 8791` 与 `SESSIONGLOW_PORT=8791 opencode`。

`sources` 还提供实际 OpenCode 服务地址、PID、项目目录与会话数。OpenChamber 可能自动启动动态端口的服务，并不一定连接 4096；插件必须在实际服务中加载。完整接入步骤见 [安装文档](docs/INSTALL.md)。`connections` 是项目插件实例数，一个服务可以产生多个连接。

## 会话列表规则

- 只列主会话。子 Agent 活动和需要确认的提示归到所属主会话，不占面板位置。
- 默认 5 个，按最近发起任务时间降序排列。工具调用、心跳和任务完成不会把老任务顶上来。
- 子任务仍活跃时，主会话不会提前变绿；任一子任务等待用户操作时，主灯管变黄。
- 主任务的终止错误保留为红色，紧随其后的 idle 事件不会将它覆盖成绿色。
- 子任务失败可能被主任务恢复，主会话的最终成功/失败以主任务结果为准。
- 完成和失败的会话留在列表中，新任务发起时才改变状态；同名会话由 ID 区分。
- 全局插件汇总已加载它的 OpenCode 实例；不是只监控当前工程。面板行下方显示项目名，悬停可查看完整标题、路径和会话 ID。

面板保存有限的本地会话摘要。插件启动时从当前项目最近的最多 32 个会话、每会话最近 12 条消息的元数据恢复近期状态，再结合实时状态校准；实时事件不等待历史回填，迟到的历史结果不会覆盖实时状态。不会读取并保存整个聊天记录。很久以前的任务或最后用户消息超出这一小段历史时，已有面板缓存优先保留排序时间，新安装首次回填可能不完整；此后的新任务时间会准确记录。

## 配置

`~/.config/sessionglow/config.json`：

```json
{
  "max_sessions": 5,
  "fps": 30,
  "opacity": 0.97,
  "intensity": 0.85,
  "always_on_top": true,
  "position": null,
  "port": 8790
}
```

菜单“外观设置”可调数量（1–12）、帧率、不透明度和动效强度，立即生效并保存。拖动后记录位置。状态缓存为 `~/.local/state/sessionglow/sessions.json`，只保留最多 512 个会话摘要。缺少配置文件时使用默认值。`--config` / `--cache` 可覆盖路径。

默认不配置开机自启。关闭窗口仅隐藏面板，可通过托盘退出整个程序。隐藏时停止绘图，事件监控仍继续。当前主要验证平台为 GNOME/X11；混合 DPI、不同桌面的托盘和 Wayland 置顶策略尚未验证。

## 开发与验证

```bash
/usr/bin/python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/plugin.test.mjs
./run.sh --render /tmp/sessionglow.png
./run.sh --demo --quit-after 10
```

`--render` 离屏绘制合成会话，不截图用户桌面。真实 OpenCode 集成测试要求已经安装插件并启动 SessionGlow：

```bash
/usr/bin/python3 tests/live_opencode.py
```

它启动独立临时 OpenCode 服务，创建两个主会话和一个子会话，通过数秒的本地 shell 命令验证插件加载、独立状态、子会话归属、完成保留和排序稳定，随后清理测试会话。不会请求模型或消耗 token。失败、等待确认及连续状态切换另由事件与动画测试覆盖。

桌面交互测试：`PYTHONPATH=. /usr/bin/python3 tests/smoke_desktop.py`，会短暂操作自己的测试面板并恢复鼠标与焦点。合成动效视频导出：`PYTHONPATH=. /usr/bin/python3 tests/render_demo.py /tmp/sessionglow.webm`（需要 ffmpeg）。

空列表不持续重绘，隐藏时只保留事件接收。五股电流增加了绘制工作，可通过外观设置降低帧率或动效强度。

源码分工：`plugin/sessionglow.mjs` 收集真实事件；`model.py` 管理会话和主子关系；`server.py` 接收本机快照；`motion.py` 计算连续动效参数；`panel.py` 绘制窗口；`__main__.py` 负责启动、配置与持久化。
