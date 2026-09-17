<div align="center">

<img src="icon.svg" width="68" height="68" alt="SessionGlow 标志" />

# SessionGlow

**让每个 OpenCode 会话，都有一盏状态灯。**

不用来回切换终端，也能一眼看见 Agent 正在工作、已经完成、发生失败，还是在等你确认。

[English](README.md) · **简体中文**

<img src="docs/assets/sessionglow-demo.gif" width="420" alt="四根会话灯管，演示运行、等待授权、模拟用户批准、恢复运行和完成" />

🔵 进行中　 🟡 待确认　 🟢 已完成　 🔴 任务失败

<sub>程序渲染的 12 秒合成演示。“Approved”表示模拟用户响应，面板本身不会代为授权。</sub>

[![Build](https://github.com/YidaHao/SessionGlow/actions/workflows/ci.yml/badge.svg)](https://github.com/YidaHao/SessionGlow/actions/workflows/ci.yml)
[![MIT](https://img.shields.io/badge/license-MIT-8B5CF6)](LICENSE)
[![Linux](https://img.shields.io/badge/platform-Linux-E95420)](#兼容性)
[![Latest release](https://img.shields.io/github/v/release/YidaHao/SessionGlow)](https://github.com/YidaHao/SessionGlow/releases/latest)

[下载 v0.1.0](https://github.com/YidaHao/SessionGlow/releases/tag/v0.1.0) · [24 fps 动效](docs/assets/sessionglow-demo.webm) · [安装指南](docs/INSTALL.md) · [使用与排查](docs/USAGE.md)

</div>

## 为什么需要 SessionGlow

同时跑几个 Agent 时，反复检查终端是否结束、有没有权限请求，会变成另一项工作。SessionGlow 把每个主会话变成桌面角落的一根灯管，让你继续专注手头的事。

- **真实事件驱动**：响应任务、错误、授权与提问事件，不根据 CPU 或终端输出猜测状态。
- **一根灯管，一个主会话**：子 Agent 的活动和确认请求归到所属主会话。
- **本地通信**：插件通过 localhost 发送有限的会话摘要。

所有光效都留在悬浮面板内部。任务创建、授权和回答仍在 OpenCode / OpenChamber 中完成。

## 灯管状态

| 状态 | 动效 | 含义 |
| --- | --- | --- |
| 🔵 进行中 | 五股舒缓交叉电流，沿线与空腔粒子漂浮 | 正在工作或自动重试 |
| 🟡 待确认 | 保持饱满波幅，增加不规则抖动 | 有权限请求或问题需要你回应 |
| 🟢 已完成 | 电流和粒子消失，绿色液体缓缓流动 | 本轮任务结束 |
| 🔴 任务失败 | 电流收成微微抖动的直线，粒子停住 | 任务终止失败或主动取消 |

状态切换约 **0.8 秒**，中途再变状态会从当前画面继续。灰色表示缺少可靠结果；断线时标明断线并调暗上次状态，不假装任务完成。

## 快速开始

### 推荐：安装 Ubuntu 软件包

从 Release 下载 [`sessionglow_0.1.0_amd64.deb`](https://github.com/YidaHao/SessionGlow/releases/download/v0.1.0/sessionglow_0.1.0_amd64.deb)，在下载目录执行：

```bash
sudo apt install ./sessionglow_0.1.0_amd64.deb
sessionglow
```

也可以从应用菜单打开 **SessionGlow**。软件包首次正常启动会为当前用户注册插件。**重启你实际使用的 OpenCode 进程**，再发起任务即可连接。演示模式可用 `sessionglow --demo`，不会注册插件。

| 使用方式 | 安装或更新插件后 |
| --- | --- |
| OpenCode 终端 | 退出后，在原项目运行 `opencode -c` |
| 独立 `opencode serve` | 等待任务结束，按原端口与认证环境重启服务 |
| OpenChamber 自动管理后台 | 等待任务结束，运行 `openchamber restart --port 3000`，替换为实际网页端口 |
| OpenChamber 连接外部服务 | 重启外部 OpenCode；刷新网页不能重载服务插件 |

OpenChamber 后台可能使用动态端口，不一定是 4096。详细步骤见 [安装指南](docs/INSTALL.md)。AppImage 属于后续计划，v0.1.0 暂不提供。

### 升级与卸载

```bash
# 关闭面板后安装新版，再打开面板并重启 OpenCode
sudo apt install ./sessionglow_X.Y.Z_amd64.deb

# 卸载前删除当前用户的插件入口
sessionglow --uninstall-plugin
sudo apt remove sessionglow
```

卸载后重启 OpenCode。配置与历史留在用户目录；如果先卸载了包，残留的受管插件入口会安全返回空结果，可手动删除 `~/.config/opencode/plugins/sessionglow.js`。包管理脚本不会修改其他用户的主目录。

## 核心功能

- **稳定排序**：默认 5 个主会话，可设 1–12 个；按最近发起任务排序，工具和心跳不打乱列表。
- **桌面悬浮**：拖动、置顶、位置保存、收起到托盘。
- **动效可调**：帧率、透明度和强度可配置；隐藏后停止绘制。
- **多实例汇总**：接入本机终端、独立服务和 OpenChamber 中已加载插件的会话。
- **恢复与重连**：保存有限摘要并通过心跳恢复；完成、失败的会话保留到被更新任务挤出。

## 事件驱动架构

OpenCode 插件处理任务和确认事件，向 `127.0.0.1:8790` 发送有数量上限的会话快照。标准库 HTTP 服务将更新放入队列，Qt 主线程负责聚合、排序和持久化；绘制层对动画参数插值，保持粒子位置连续。

插件每 5 秒发送心跳，约 20 秒无更新则标为断线。历史回填与实时事件分开执行，不阻塞新任务；面板关闭也不阻塞 Agent 工具。

## 主会话与子 Agent

只为主会话分配灯管。子任务的权限/问题会让所属主灯管变黄；子任务完成不会让仍在运行的主任务变绿。可恢复的子任务或工具错误不等于主任务失败，主任务终止错误则会保留，不被随后的 idle 覆盖。

排序使用任务发起时间；只查看旧聊天不会置顶。悬停可查看完整标题、项目目录和会话 ID。

## 兼容性

| 平台 | 状态 |
| --- | --- |
| Ubuntu 22.04.5 / GNOME 42.9 / X11 / amd64 | ✅ v0.1.0 已验证目标 |
| Ubuntu 24.04 / GNOME / Wayland | ⚠️ 未验证，计划后续测试 |
| KDE Plasma | ⚠️ 未验证 |
| 混合 DPI | ⚠️ 未验证 |
| macOS | ❌ 本版本不支持 |
| Windows | ❌ 本版本不支持 |

| 接入方式 | 状态 |
| --- | --- |
| OpenCode 终端 | ✅ 已在 1.18.31 验证 |
| `opencode serve` | ✅ 已在 1.18.31 验证，包括认证服务 |
| OpenChamber | ✅ 自动管理与外部服务两种模式均已验证 |

容器离屏测试不代表 Wayland 桌面已验证。Python、PyQt5 和 Qt 保留各自许可证，MIT 适用于本项目自己的代码。

## 隐私

插件通过 localhost 通信，**不向面板发送提示词正文、回答正文、工具参数或服务凭据**。快照包括会话标题、ID、父子关系、项目路径、状态、时间和来源诊断。标题本身可能含有用户或 OpenCode 提供的文字。

首次连接会查询有限的 OpenCode 近期记录，并使用消息元数据恢复状态。面板最多保存 512 个摘要到 `~/.local/state/sessionglow/sessions.json`。没有遥测，默认不设置开机自启。

## 配置

菜单可修改数量、置顶和外观，保存到 `~/.config/sessionglow/config.json`：

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

手工编辑后重新启动面板。更改接收端口时，同时在 OpenCode 的启动环境中设置 `SESSIONGLOW_PORT`。

<details>
<summary>诊断与常用命令</summary>

```bash
sessionglow --version
sessionglow --install-plugin
sessionglow --demo --quit-after 15
sessionglow --render /tmp/sessionglow.png
curl -s http://127.0.0.1:8790/health | /usr/bin/python3 -m json.tool
```

`sources` 列出实际服务地址、PID 和项目；`connections` 统计项目插件实例，不等于服务器数量。终端可见但 OpenChamber 不可见时，核对并重启真正使用的后台服务。

</details>

## 开发与贡献

源码安装：

```bash
git clone https://github.com/YidaHao/SessionGlow.git
cd SessionGlow
sudo apt install python3-pyqt5
/usr/bin/python3 install.py
./run.sh
```

欢迎贡献。环境、测试、打包、事件调试与新平台验证见 [CONTRIBUTING.md](CONTRIBUTING.md)。后续兼容性与打包任务见 [Roadmap Issues](https://github.com/YidaHao/SessionGlow/issues?q=is%3Aissue+label%3A%22help+wanted%22)。

| 文档 | 内容 |
| --- | --- |
| [安装指南](docs/INSTALL.md) | 软件包、源码、升级、卸载与 OpenChamber 接入 |
| [使用与排查](docs/USAGE.md) | 控制、排序、外观与连接诊断 |
| [动效素材](docs/assets/README.md) | 短演示与 Social Preview 的生成方式 |
| [v0.1.0 说明](docs/releases/v0.1.0.md) | 发布范围、兼容性和已知限制 |

[MIT License](LICENSE) · Copyright © 2026 YidaHao
