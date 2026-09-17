# SessionGlow 开源项目三阶段发布计划

> 目标：不要一次性把项目直接推向大流量，而是通过 **仓库准备 → Soft Launch → 正式 Launch** 三个阶段，逐步完成产品化、验证和传播。

---

## 总体思路

SessionGlow 当前最适合的定位是：

> **Ambient status lights for your OpenCode agents.**

核心价值不是“管理 Agent”，而是：

> **让用户不用频繁切换终端，也能一眼看出哪些 Agent 正在工作、已经完成、发生失败，或者正在等待人工确认。**

因此整个发布流程的重点不是单纯“发帖求 Star”，而是先把：

**看懂 → 想试 → 能装 → 能正常使用 → 愿意传播**

这条链路打通。

---

# 第一阶段：仓库准备

## 阶段目标

在正式宣传之前，把 SessionGlow 从“开发者项目仓库”整理成“第一次进入 GitHub 就能看懂并快速安装的开源产品”。

这一阶段原则上 **不做大规模宣传**。

---

## 1. 明确一句话定位

README、GitHub About、Social Preview 和后续宣传文案统一使用同一套定位。

推荐：

> **Ambient status lights for your OpenCode agents.**

辅助说明：

> See which agents are working, done, failed, or waiting for you — without switching terminal tabs.

中文可以继续保留：

> **让每个 OpenCode 会话，都有一盏状态灯。**

### 定位原则

不要把 SessionGlow 定义为：

- OpenCode Session Manager
- OpenCode Dashboard
- Agent Orchestrator

因为这些名称会让用户期待：

- 创建和管理 Session
- Worktree 管理
- Review Diff
- Token / Cost 分析
- Agent 编排
- Terminal 管理

SessionGlow 更适合聚焦：

> **Observe，而不是 Manage。**

---

## 2. 添加 MIT LICENSE

仓库根目录增加：

```text
LICENSE
```

推荐使用 MIT License。

目的：

- 明确项目是真正可复用、可修改、可分发的开源项目；
- 降低其他开发者参与和二次开发的法律顾虑；
- 提升仓库完整度。

---

## 3. 完善 GitHub 仓库门面

### GitHub About

推荐 Description：

> **Ambient status lights for parallel OpenCode agents.**

或者：

> **A lightweight desktop status display for parallel OpenCode agents.**

### GitHub Topics

建议至少添加：

```text
opencode
ai-agent
coding-agent
developer-tools
agent-monitoring
linux
desktop-widget
pyqt
```

### Social Preview

建议制作一张简洁的预览图：

- SessionGlow Logo
- 3～5 根不同状态的灯管
- 一句话：

> **See every OpenCode agent at a glance.**

避免堆大量文字。

---

## 4. 默认 README 改成英文

推荐文件结构：

```text
README.md
README.zh-CN.md
```

其中：

- `README.md`：英文，作为 GitHub 默认首页；
- `README.zh-CN.md`：中文。

README 顶部提供语言切换：

```text
English | 简体中文
```

---

## 5. 重构 README 首屏

README 的首屏应该在 10～15 秒内回答三个问题：

1. 这是什么？
2. 为什么需要？
3. 它长什么样？

推荐首屏结构：

```markdown
# SessionGlow

Ambient status lights for your OpenCode agents.

See which agents are working, done, failed, or waiting for you
— without switching terminal tabs.

English | 简体中文

[Demo GIF]

🔵 Working   🟡 Needs you   🟢 Done   🔴 Failed
```

然后再放少量 Badge：

```text
MIT
Linux
OpenCode
Latest Release
```

不要在首屏堆十几个 Badge。

---

## 6. 制作 6～12 秒 Demo GIF

GIF 是 SessionGlow 最重要的传播素材之一。

### 推荐演示内容

在 6～12 秒内体现：

1. 多个 OpenCode Session 同时运行；
2. 多根灯管显示不同状态；
3. 某个 Session 从 Working 变为 Needs You；
4. 用户处理 Permission / Question；
5. 状态恢复 Working；
6. 最终变为 Done。

### 原则

- 自动循环；
- 尽量无文字，或只有极少文字；
- 视觉上能够独立解释产品；
- README、Reddit、X、HN 都能复用。

---

## 7. 调整 README 信息顺序

推荐 README 顺序：

```text
1. Hero / 一句话定位
2. Demo GIF
3. Why SessionGlow
4. 状态含义
5. Quick Start
6. Core Features
7. Event-driven Architecture
8. Main/Sub-agent Aggregation
9. Compatibility
10. Privacy
11. Configuration
12. Development / Contributing
```

### README 上半部分服务普通用户

重点回答：

- 为什么需要？
- 能不能用？
- 怎么安装？

### README 下半部分服务开发者

包括：

- 动画实现细节；
- 配置项；
- 调试命令；
- 测试方法；
- 开发环境。

---

## 8. 突出三个核心卖点

### Event-driven, not guessed

推荐描述：

> SessionGlow listens to OpenCode task, failure, permission, and question events instead of inferring agent activity from CPU usage or terminal output.

强调：

- 状态来自真实 OpenCode 事件；
- 不是 CPU polling；
- 不是通过终端输出猜测状态。

---

### One light, one session

推荐描述：

> Sub-agent activity is rolled up into its parent session, including attention requests.

即：

- 一根灯管对应一个主 Session；
- 子 Agent 状态汇总到主 Session；
- 子 Agent 的 Permission / Question 同样可以触发提醒。

---

### Local by design

推荐描述：

> SessionGlow communicates over localhost. Prompt contents, model responses, tool arguments, and service credentials are not sent to the panel.

强调：

- 本地通信；
- 不上传 Prompt；
- 不上传模型 Response；
- 不传 Tool Arguments；
- 不传密码或凭据。

---

## 9. 增加 Compatibility Matrix

不要只用一段文字描述兼容性。

推荐：

| Platform | Status |
|---|---|
| Ubuntu 22.04 / GNOME / X11 | ✅ Tested |
| Ubuntu 24.04 / GNOME / Wayland | 🚧 Testing |
| KDE Plasma | ⚠️ Untested |
| macOS | ❌ Not supported yet |
| Windows | ❌ Not supported yet |

Integration：

| Integration | Status |
|---|---|
| OpenCode terminal | ✅ |
| `opencode serve` | ✅ |
| OpenChamber | ✅ |

让用户可以快速判断自己是否适用。

---

## 10. 简化安装流程

正式宣传之前，最好不要把：

```bash
git clone
cd SessionGlow
sudo apt install ...
python install.py
```

作为唯一安装方式。

至少提供：

```text
sessionglow_0.1.0_amd64.deb
```

最好再提供：

```text
SessionGlow-x86_64.AppImage
```

### README 安装顺序

优先展示：

1. `.deb`
2. AppImage
3. Build from source

源码安装应下沉到开发者章节。

---

## 11. 补完整的升级与卸载流程

用户需要知道：

### 如何升级

例如：

```bash
sudo apt install ./sessionglow_x.x.x_amd64.deb
```

### 如何卸载

例如：

```bash
sudo apt remove sessionglow
```

如果 SessionGlow 会安装 OpenCode plugin，也要明确说明：

- plugin 文件位置；
- 卸载时是否自动清理；
- 如何手动清理。

---

## 12. 加 CI

建议 GitHub Actions 至少完成：

- Python tests；
- Node tests；
- 基础 lint；
- 构建检查。

目标是在 README 上看到：

> Build: Passing

这样第一次访问仓库的人会更有信心。

---

## 13. 添加 CONTRIBUTING.md

把 README 中过于开发者向的内容逐步移到：

```text
CONTRIBUTING.md
```

包括：

- 开发环境；
- 测试方式；
- 代码结构；
- 提交规范；
- 如何添加新平台；
- 如何调试 OpenCode event。

README 只保留：

> Contributions are welcome. See `CONTRIBUTING.md`.

---

## 14. 增加 Issue Template 和 Roadmap Issue

可以把已经明确的后续任务公开为真实 Issue，例如：

- Wayland support
- AppImage package
- Click a session to focus its terminal
- Custom notification sounds
- macOS support
- Windows support

适合外部贡献的 Issue 可添加：

```text
help wanted
good first issue
```

不要为了制造活跃度而创建大量无意义 Issue。

---

## 15. 发布 v0.1.0 Release

第一版 Release 不必追求支持全部 Linux 环境。

可以明确限定：

> **v0.1.0 — Ubuntu / GNOME / X11**

Release 中至少包含：

- Release Notes；
- `.deb`；
- AppImage（如已完成）；
- 已知限制；
- Compatibility；
- Upgrade / Uninstall 说明。

---

## 第一阶段完成标准

在进入 Soft Launch 前，最好满足：

- [x] MIT LICENSE
- [x] 英文 README 为默认首页
- [x] 中文 README
- [x] Demo GIF
- [ ] GitHub About
- [ ] Topics
- [ ] Social Preview
- [x] `.deb`
- [ ] AppImage（建议）
- [x] Compatibility Matrix
- [x] Upgrade / Uninstall
- [x] CI 通过
- [x] CONTRIBUTING.md
- [x] Roadmap Issues
- [x] v0.1.0 Release

执行记录与可验证链接见 [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md)。[v0.1.0 已发布](https://github.com/YidaHao/SessionGlow/releases/tag/v0.1.0)，CI 与 Release 安装包校验均通过；Roadmap #1–#3 已创建。AppImage 建议项暂缓。当前仍缺 GitHub About、Topics 的管理授权，以及将已生成的 Social Preview 图上传到仓库设置，因此第一阶段尚未全项关闭。

---

# 第二阶段：Soft Launch

## 阶段目标

这一阶段的目标 **不是刷 Star**。

真正目标是：

> 找到真实用户环境里的安装、兼容性和状态同步问题。

建议先获得：

> **5～20 个真实用户**

再进入大规模发布。

---

## 1. 首批发布渠道

只投放到高相关、小范围社区：

- OpenCode Discord / Community
- `r/opencode`
- OpenCode GitHub Discussions
- 熟悉 OpenCode 的朋友
- 少量 Linux / AI Coding Agent 用户

暂时不急着：

- Product Hunt
- 大范围 X 宣传
- Hacker News 首页级曝光

---

## 2. Soft Launch 文案重点

不要写：

> 我做了一个非常酷的 Agent Monitor，欢迎 Star。

推荐从痛点切入：

> I run several OpenCode sessions in parallel and kept missing permission prompts, so I built a tiny always-on-top status display.

然后：

- 放 GIF；
- 放一句定位；
- 给 GitHub 地址；
- 明确当前平台支持情况。

---

## 3. 收集重点问题

Soft Launch 期间重点观察以下类别。

### 安装问题

- Python / PyQt 依赖；
- `.deb` 安装；
- AppImage；
- plugin 自动安装；
- 权限问题。

### OpenCode 兼容性

- 不同 OpenCode 版本；
- `opencode serve`；
- OpenChamber；
- 多 Session；
- 子 Agent；
- Permission / Question。

### Linux Desktop

- GNOME；
- KDE；
- X11；
- Wayland；
- 多显示器；
- High DPI；
- Mixed DPI；
- always-on-top。

### 状态准确性

重点检查：

- Working → Done
- Working → Failed
- Working → Needs You
- Needs You → Working
- 子 Agent → 主 Session 聚合

---

## 4. 优先处理 Wayland

Wayland 不一定是 v0.1.0 的发布前置条件。

但是如果 Soft Launch 中大量用户遇到 Wayland 问题，那么应该把：

> **Wayland support**

提升为正式 Launch 的高优先级门槛。

推荐策略：

### v0.1.0

```text
Ubuntu / GNOME / X11
```

### v0.2.0

```text
Wayland support
```

这样可以先发布，再根据真实反馈决定优先级。

---

## 5. 根据反馈调整 README

Soft Launch 后，README 往往会暴露真正缺失的信息。

例如用户反复问：

> Does this work on Wayland?

那就把 Wayland 放到 Compatibility 更显眼的位置。

用户反复问：

> Does it read my prompts?

那就把 Local by design 提前。

README 应该根据真实 FAQ 调整，而不是只根据作者视角设计。

---

## 6. 修复高频问题后发布补丁版本

根据反馈可以发布：

```text
v0.1.1
v0.1.2
```

优先修：

1. 安装失败；
2. 状态错误；
3. 崩溃；
4. Wayland / DPI；
5. OpenCode 版本兼容。

不要优先加大功能。

---

## 第二阶段完成标准

进入正式 Launch 前，希望达到：

- [ ] 已有 5～20 个真实用户
- [ ] 安装路径基本稳定
- [ ] `.deb` 可以正常使用
- [ ] 主要 OpenCode 状态转换已验证
- [ ] 已明确 Wayland 状态
- [ ] 已修复高频安装问题
- [ ] README FAQ 已根据反馈调整
- [ ] 至少发布一个稳定 Release
- [ ] CI 持续通过
- [ ] Issues 中不存在明显阻塞性 Bug

---

# 第三阶段：正式 Launch

## 阶段目标

当项目已经做到：

> 看得懂、装得上、状态准、已有人真实使用

再集中获取曝光。

此时才真正追求：

- GitHub Stars；
- Contributors；
- Issues；
- 用户反馈；
- 社区认知。

---

## 1. 提交 awesome-opencode

建议在大规模宣传前提交。

推荐描述：

> **SessionGlow** — Ambient desktop status lights for parallel OpenCode sessions, showing working, completed, failed, and attention-needed states.

目的：

- 获得精准 OpenCode 流量；
- 增强项目可信度；
- 形成长期入口。

---

## 2. Reddit

重点：

```text
r/opencode
```

也可以选择：

- AI coding agent 相关社区；
- Linux desktop；
- developer productivity 社区。

推荐标题思路：

> I run several OpenCode agents in parallel and kept missing permission prompts, so I built SessionGlow

正文：

1. 痛点；
2. 10 秒 GIF；
3. 一句话介绍；
4. 为什么是 event-driven；
5. 当前支持平台；
6. GitHub。

不要以：

> Please star my project

作为主要诉求。

---

## 3. Show HN

推荐标题：

> **Show HN: SessionGlow – Ambient status lights for parallel OpenCode agents**

HN 正文重点讲技术和动机：

1. 为什么做；
2. 多 Agent 并行时的问题；
3. OpenCode 事件怎么获取；
4. 为什么不用 CPU polling；
5. 主/子 Agent 怎么聚合；
6. localhost 通信；
7. 隐私；
8. GitHub。

HN 用户对实现细节的兴趣通常高于纯视觉宣传。

---

## 4. X / Twitter

最适合直接展示视觉效果。

推荐内容：

```text
5 OpenCode sessions running.

I got tired of checking terminal tabs just to know:
- Is it still working?
- Did it finish?
- Is it waiting for me?

So I built SessionGlow.

Each agent gets a status light on your desktop.
```

配：

> 6～12 秒 GIF / MP4

视频本身是主角，文案不要过长。

---

## 5. 中文社区同步

可以同步投放：

- Linux.do
- V2EX
- 知乎
- 掘金
- B站

推荐标题：

> **同时跑 5 个 OpenCode Agent，总忘记哪个在等我，所以我给每个 Agent 做了一盏“状态灯”**

不要只写：

> 开源了一个 OpenCode Session Monitor

前者更容易让用户理解真实使用场景。

---

## 6. Product Hunt 暂缓到后续

Product Hunt 不建议作为第一波正式 Launch 的核心渠道。

更适合等：

- 安装体验成熟；
- Wayland 基本支持；
- 有更多用户；
- 有真实 testimonial；
- macOS / Windows 或更多 Agent 支持；

再进行一次更产品化的 Launch。

---

# 推荐的完整执行顺序

最终推荐顺序：

```text
01. 明确一句话定位
02. MIT LICENSE
03. GitHub About / Topics / Social Preview
04. 英文 README
05. 中文 README
06. 重构 README Hero
07. 制作 6～12 秒 GIF
08. Compatibility Matrix
09. .deb
10. AppImage
11. Upgrade / Uninstall
12. CI
13. CONTRIBUTING.md
14. Issue Template / Roadmap
15. v0.1.0 Release

---- Soft Launch ----

16. OpenCode 社区小范围发布
17. 邀请 5～20 个真实用户
18. 修安装问题
19. 修状态同步问题
20. 验证 Wayland / KDE / DPI
21. 根据真实 FAQ 修改 README
22. 发布 v0.1.x

---- Formal Launch ----

23. PR 到 awesome-opencode
24. r/opencode
25. Show HN
26. X / Twitter
27. Linux.do / V2EX / 知乎 / 掘金
28. 后续再考虑 Product Hunt
```

---

# 当前最值得优先做的五件事

如果现在开始执行，建议优先级是：

## P0

1. **MIT LICENSE**
2. **英文 README + 中文 README**
3. **重做 README Hero + Demo GIF**

## P1

4. **`.deb` + v0.1.0 Release**
5. **做一次 Soft Launch**

Wayland 可以紧随其后，根据 Soft Launch 的真实反馈决定是否作为全网正式 Launch 的前置条件。

---

# 发布原则

整个过程中始终坚持：

> **不要过早追求曝光，先提高流量进入仓库后的转化率。**

对于 SessionGlow 来说，更重要的漏斗是：

```text
看到帖子
   ↓
理解产品
   ↓
被 GIF 吸引
   ↓
进入 GitHub
   ↓
10 秒内看懂
   ↓
1 分钟内完成安装
   ↓
真实运行成功
   ↓
Star / Issue / Share
```

真正决定项目能不能传播开的，不只是“去哪发”，而是这条链路是否顺畅。
