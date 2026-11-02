# 🤖 ATMOSPHERE-PANEL AI 开发总纲与行为守则

> **致所有 AI 助手**

## 一、🚨 最高安全铁律（绝对不准违反）

1. **禁止全盘重写**：每次修改文件不能把覆盖整个页面, 就算大改也得先说同意了也行
2. **修改核心环境配置**：最好不要动 `nuxt.config.ts`、`package.json`、`requirements.txt`（除非明确要求加依赖）。

## 二、📦 项目基础架构

本项目兼容win/macos/Linux

- 前端：Nuxt 4.6.x + Vue 3.5 + TypeScript + Tailwind CSS v4 + vite，位于 frontend/。
- 后端：FastAPI + SQLite，位于 backend/，入口为 backend/app/main.py → main_refactored.py。
- Windows 开发端口：FastAPI 27777；前端 /api 代理到 27777。
- 数据库：backend/app/panel.sqlite3；实例文件：backend/data/servers/<instance_id>/。
- 后端路由包括 auth、resources、instances、deployments、console、files/backups；进程管理位于 backend/app/infra/process_manager.py。

## 🧱 核心组件教程：`<AtmosphereCard>` 使用规范与守则

`<AtmosphereCard>` 是 ATMOSPHERE-PANEL 的核心 UI 基石。它封装了极度复杂的半透明毛玻璃、双层错位阴影和独立边框控制。
**核心目的**：解决“调色板污染卡片背景”和“微调边框极其痛苦”的历史遗留问题。

### 🚨 强制守则（AI 必须遵守）

1. **全站统一**：在编写任何页面（如 `login.vue`, `dashboard.vue`, `[id].vue`）时，**严禁**手写 `<div class="bg-xxx border-xxx">` 作为卡片外壳，**必须且只能**使用 `<AtmosphereCard>`。
2. **剥离调色板**：严禁在 `<AtmosphereCard>` 内部或外部使用全局的 `bg-surface` 类名。卡片的底色必须由组件的 Props 控制，默认自带极简半透明色。
3. **内容插槽**：所有的页面内容、表单、图表，必须放置在 `<AtmosphereCard> ... </AtmosphereCard>` 的默认插槽内部。
4. **极简传参**：除非有明确的视觉需求，否则**直接使用默认标签** `<AtmosphereCard>内容</AtmosphereCard>`，不要乱传参数破坏默认的毛玻璃质感。

## 📌 项目概况

- **项目名**：ATMOSPHERE-PANEL（一个极致暗黑科幻风的 Minecraft 面板）。
- **技术栈**：Nuxt 4 (Vue 3 + TS) + Tailwind CSS v4 (CSS-first) + FastAPI + SQLite。
- **环境**：Windows 本地开发，未来部署 win/Linux/macos（已重构跨平台 ProcessManager）。
- **UI 风格**：参考 RhineLab/CatBot-3，四色系统，星空背景，高度定制的玻璃态卡片。

我们已完成的战绩

1. 前端 UI 已经达到商业级绝美水平（Tailwind v4 迁移成功，解决了背景色被调色板污染的问题）。
2. 成功封装了 `<AtmosphereCard>` 组件，支持四边独立控制、透明度、偏移量等 Prop 传参。
3. 后端架构已分层完毕（routers/services/infra），集成了 `aio-mc-rcon`（解决同步阻塞），封装了跨平台的真实 Java 进程管理。
4. 配置了 `AI_INSTRUCTIONS.md` 作为 AI 开发守则。

---

## 当前实现状态与交接摘要（2026-11）

### 已完成能力

- Cookie Session 登录、/api/me、登出和 auth middleware。
- Dashboard、实例列表、详情、主机指标、控制台、文件与备份基础界面。
- 跨平台 ProcessManager：Linux 使用 systemd，Windows/macOS 使用 Java 子进程。
- AtmosphereCard 默认玻璃视觉：左/上边框、右/下留空、半透明背景、偏移阴影和悬浮状态。
- mc_meta_service.py：FastMirror 根目录映射、版本/构建/下载 URL 解析、官方回退和缓存。
- 资源路由：/api/resources/cores、/versions、/builds、/download。
- 部署接口：POST /api/instances/deploy、GET /api/instances/deploy/stream/{id}；任务先写 SQLite，再下载、落盘配置并启动进程。
- FastMirror 已确认字段：根列表 data[].name；版本 data.mc_versions；构建 data.builds[].core_version；下载 data.download_url。
- 前端核心选择已接入真实版本/构建接口，核心目录包含 Paper、Forge、NeoForge、Fabric、Arclight、CatServer、Quilt、Folia、Leaves、Purpur、Spigot、Sponge、代理、基岩和 Vanilla 等。

### 当前最重要的未完成/风险项

1. 登录转场尚未完成视觉验收。目标是 auth success → 硬切鉴权文字 → 外层透明壳自上而下扫描擦除 → 内层玻璃实体化/扩张 → Dashboard 交接。必须清理重复旧动画、克隆层、AuthOverlay、route overlay，避免多套动画竞争。
2. 登录页存在 login-transition-outer、login-transition-inner、login-glass-card 实验结构；外层与内层必须保持兄弟层，分别动画，不能对包含文字/输入框的父层做大倍数 scale。
3. 部署历史上出现过空目录、错误 100%、SQLite 端口冲突和详情 404。部署失败必须显示真实错误并把数据库状态设为 error；禁止伪造成功。
4. 数据库曾被清理并备份为 panel.sqlite3.bak-20261101 一类文件；重置数据库必须先备份并明确告知，不得无确认执行。
5. active 部署页是 frontend/app/pages/deploy.vue；NewInstanceWizard.vue / DeployLayout.vue 属于旧链路，仍可能残留旧 API 或硬编码，修改前必须确认入口和引用关系。

### 交接验收清单

- 前端：pnpm build。
- 后端：使用 Windows venv 执行 .venv/Scripts/python.exe -m py*compile app/routers/*.py app/services/\_.py。
- 登录转场：正常登录、失败、重复点击、慢网、刷新、后退、reduced-motion；确认无白闪、无残留遮罩、焦点可用。
- 部署：确认 POST/SSE/SQLite/文件系统/ProcessManager 全链路；成功必须有真实 jar、eula.txt、server.properties；失败必须保留 error 记录和 traceback。
- 资源：确认 FastMirror 真实响应结构，不猜字段、不返回假数组；版本和构建可渲染、可选择，下载 URL 不自行拼接。

### 后续 AI 工作纪律

- 先读本文件、当前文件和真实运行日志，再修改；不要依据旧 SDADA 总结推断现状。
- 不要重写整页，不要乱改 nuxt.config.ts、package.json、requirements.txt，有想法可以提, 用户明确批准。
- 任何动画或部署成功声明都必须有可验证证据；构建通过不等于浏览器视觉通过，也不等于部署链路通过。

### 📖 常用使用场景与代码示例

#### 场景 1：默认科幻卡片（登录页风格，左上亮边，右下无边框）

```vue
<!-- 什么都不传，即可获得最经典的玻璃态 -->
<AtmosphereCard>
  <div class="text-text-primary">你的内容</div>
</AtmosphereCard>
```

场景 2：全包围细线边框（仪表盘数据块风格）
如果你需要一个四周都有细细白线的边框（例如顶部的 ACTIVE INSTANCES 数据卡）：

vue
<AtmosphereCard
:border-bottom="true"
:border-right="true"
variant="glass-light"

>

  <h3>ACTIVE INSTANCES</h3>
</AtmosphereCard>

场景 3：极度定制（比如警告红框、或者是特定的悬浮阴影）
如果你的设计需要特别强烈的反差，或者极深的阴影：

vue
<AtmosphereCard
bg-color="rgba(255, 0, 0, 0.1)"
border-color="rgba(255, 0, 0, 0.3)"
:shadow-offset-x="6"
:shadow-offset-y="6"
shadow-color="rgba(255,0,0,0.2)"

>

  <h3 class="text-red-500">危险警告</h3>
</AtmosphereCard>

场景 4：无阴影的扁平卡片
vue
<AtmosphereCard :has-shadow="false">

  <!-- 内容 -->
</AtmosphereCard>

⚙️ 组件 API 全量速查表（Props）
Prop 名称 类型 默认值 说明
variant String 'glass' 预设模式：'glass' (深透黑), 'glass-light' (极淡白透), 'solid' (实心，慎用)
bgColor String '#000000' 背景基础色（十六进制或 rgb）
bgOpacity Number 0.2 背景透明度（0 到 1 之间）
borderColor String rgba(255,255,255,0.2) 边框颜色
borderWidth Number 1 边框粗细
borderTop Boolean true 是否显示顶部边框
borderLeft Boolean true 是否显示左侧边框
borderBottom Boolean false 是否显示底部边框
borderRight Boolean false 是否显示右侧边框
hasShadow Boolean true 是否开启底部向右下的偏移错位阴影
shadowOffsetX Number 3 阴影 X 轴偏移像素
shadowOffsetY Number 3 阴影 Y 轴偏移像素
shadowColor String rgba(255,255,255,0.05) 阴影边框颜色

注：组件已启用 inheritAttrs: false 并自动透传 $attrs，如果以上 Props 仍无法满足特殊需求，你可以且仅可以使用 class 进行最终覆盖微调（如 <AtmosphereCard class="bg-black/50 backdrop-blur-2xl">）。
