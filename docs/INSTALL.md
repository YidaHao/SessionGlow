# 安装与接入

SessionGlow 分为两个部分：Ubuntu 桌面上的悬浮面板，以及运行在 OpenCode 进程中的插件。插件把真实会话状态发给面板；仅打开面板不会自动发现其他进程里的任务。

已验证：Ubuntu 22.04.5、GNOME/X11、Python 3.10、PyQt5、OpenCode 1.18.31。无需编译或安装 npm 依赖。

## 1. 准备依赖

```bash
sudo apt install python3-pyqt5
```

当前机器已安装。启动器使用 `/usr/bin/python3`，不受 Conda 或虚拟环境切换影响。OpenCode 需要能在终端通过 `opencode --version` 运行。

## 2. 安装插件和应用菜单入口

在仓库根目录执行：

```bash
/usr/bin/python3 install.py
```

当前仓库位置是 `~/Workspace/SessionGlow`，也可以使用完整路径：

```bash
/usr/bin/python3 ~/Workspace/SessionGlow/install.py
```

安装内容：

| 文件 | 用途 |
| --- | --- |
| `~/.config/opencode/plugins/sessionglow.js` | OpenCode 全局插件入口，引用仓库里的 `plugin/sessionglow.mjs` |
| `~/.local/share/applications/sessionglow.desktop` | Ubuntu 应用菜单入口 |

不需要 `sudo`。安装器保留现有 `opencode.json` 和其他插件。仓库移动后，需核对并更新插件入口中的绝对路径；安装器遇到内容不同的已有入口会提示，不会直接覆盖。

从此前的 WindowRag 切换时使用：

```bash
/usr/bin/python3 ~/Workspace/SessionGlow/install.py --replace-windowrag
```

旧入口会改名为 `windowrag.js.disabled`。同时从旧程序的托盘退出 WindowRag。

## 3. 打开面板

```bash
~/Workspace/SessionGlow/run.sh
```

或在 Ubuntu 应用菜单搜索 **SessionGlow**。只运行一个真实面板即可；重复启动会报告 8790 端口占用。先看效果可以运行 `run.sh --demo`，但演示模式不接收真实会话。

## 4. 根据 OpenCode 启动方式接入

### 终端直接运行 OpenCode

安装插件后，退出并重新启动 OpenCode。在你原来的项目目录运行：

```bash
opencode -c
```

`-c` 继续最近的会话。面板无需跟着重启。发起任务后相应灯管应变为蓝色。

### 独立服务：`opencode serve --port 4096`

插件必须加载在 **服务端进程** 中。仅刷新浏览器、重启客户端或在另一个终端启动 OpenCode，不会更新这个已运行的服务。

等待该服务上的任务结束，在运行它的终端按 Ctrl+C，然后按原配置重新启动：

```bash
opencode serve --hostname 127.0.0.1 --port 4096
```

如果原服务使用 `OPENCODE_SERVER_PASSWORD`、`OPENCODE_SERVER_USERNAME` 或其他配置环境变量，重新启动时沿用它们。由 systemd 等进程管理器运行的服务，应通过原管理器重启，保留原有配置。

OpenCode 按项目目录初始化插件。在客户端打开你要看的项目/会话后，插件会回填近期会话并开始上报。面板默认只列最近发起任务的 5 个主会话。

### OpenChamber 自动管理的 OpenCode

OpenChamber 可以自行启动一个使用动态端口的 OpenCode 服务。**它不一定连接你另开的 4096 服务。** 安装插件后，等待任务结束，通过 OpenChamber 自身重启其管理的后台：

```bash
openchamber status
openchamber restart --port 3000
```

`3000` 是 OpenChamber 网页端口，不是 OpenCode API 端口；如果你的网页使用其他端口，请替换。刷新页面并打开对应项目。重启后自动管理的 OpenCode API 端口可能变化。

如果 OpenChamber 连接的是外部服务，重启 OpenChamber 通常只重连，并不会重启外部 OpenCode。此时还需按上一节重新启动对应服务。

### 明确让 OpenChamber 使用已有的 4096 服务

先运行外部服务，再用以下环境启动 OpenChamber：

```bash
# 终端一：使用你原有的 OpenCode 配置和认证环境
opencode serve --hostname 127.0.0.1 --port 4096

# 终端二：同样沿用外部服务的认证环境
OPENCODE_HOST=http://127.0.0.1:4096 OPENCODE_SKIP_START=1 \
  openchamber serve --port 3000
```

如果 3000 上已经有 OpenChamber，先等待任务结束并用 `openchamber stop --port 3000` 停止，再按上面的方式启动。独立服务开启密码时，OpenChamber 启动环境中的用户名/密码也必须与它一致；不要将密码写入仓库或文档。

以上参数已核对本机 `openchamber --help`。不同版本可先检查帮助中的 `OPENCODE_HOST`、`OPENCODE_PORT` 和 `OPENCODE_SKIP_START`。

## 5. 验证连接和实际来源

```bash
curl -s http://127.0.0.1:8790/health | /usr/bin/python3 -m json.tool
```

检查返回值：

- `connections`：有效的项目插件连接数量。一个服务可初始化多个项目，所以它不等于服务数或会话数。
- `sources`：各连接的 `endpoint`、`pid`、`directory`、`session_count` 和心跳时间。
- `sessions`：面板当前显示的主会话、状态、项目目录和连接情况。
- `max_sessions`：当前显示数量上限。

例如 `sources[].endpoint` 为 `127.0.0.1:4096`，才证明有来自这个服务的插件连接。动态端口的地址也会在这里显示。旧版本插件的来源字段可能为空，完整重启对应 OpenCode 后更新。

桌面面板与插件必须属于同一个本机用户环境，且插件发送端口一致。服务若运行在其他用户、容器或远程机器中，不会使用本用户的 `~/.config/opencode/plugins/`；本版本默认只覆盖本机接入。

## 自定义面板端口

OpenCode API 端口和 SessionGlow 接收端口是不同概念。默认前者可能是 4096，后者固定为 8790。

```bash
# 面板
~/Workspace/SessionGlow/run.sh --port 8791

# OpenCode 终端
SESSIONGLOW_PORT=8791 opencode

# 或 OpenCode 服务，API 仍使用 4096
SESSIONGLOW_PORT=8791 opencode serve --hostname 127.0.0.1 --port 4096
```

由 OpenChamber 自动启动的服务需从 OpenChamber 启动环境继承 `SESSIONGLOW_PORT`。

## 更新与卸载

只改灯管绘制：退出并重新打开 SessionGlow 即可。

修改 `plugin/sessionglow.mjs`：完整重启对应的 OpenCode 服务或终端。仅重新访问项目或调用 `/instance/dispose` 不能保证清除模块缓存；不要用它代替插件升级后的完整重启。

卸载时，先从面板菜单退出，然后移除本程序的两个安装入口：

```bash
rm ~/.config/opencode/plugins/sessionglow.js
rm ~/.local/share/applications/sessionglow.desktop
```

再重启 OpenCode。仓库、`~/.config/sessionglow/` 配置和 `~/.local/state/sessionglow/` 历史摘要会保留，按需自行清理。程序默认不会设置开机自启。

下一步：[日常使用与排查](USAGE.md)。
