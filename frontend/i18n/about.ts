type Locale = 'zh' | 'en' | 'ja'
const text: Record<string, Record<Locale, () => string>> = {
  aboutTitle: {
    zh: () => '关于 ATMOSPHERE',
    en: () => 'ABOUT ATMOSPHERE',
    ja: () => 'ATMOSPHERE について',
  },
  // 简介文案可直接换行，渲染时会去掉模板缩进。
  aboutIntro: {
    zh: () =>
      `ATMOSPHERE-PANEL 是一个开源且实用的 Minecraft 服务器管理面板，其基于 Web 技术，通过受身份验证保护的界面，可以注册服务器实例、选择服务端核心与版本并由后端 API 完成部署与运行管理。`,
    en: () =>
      'ATMOSPHERE-PANEL is an open-source, web-based Minecraft server management panel. Behind an authenticated interface you can register instances, choose server cores and versions, and let the backend API handle deployment and runtime management.',
    ja: () =>
      'ATMOSPHERE-PANEL はオープンソースの Web ベースの Minecraft サーバー管理パネルです。認証された画面からインスタンス登録、サーバーコアとバージョンの選択、バックエンド API によるデプロイと稼働管理を行えます。',
  },
  aboutGithub: {
    zh: () => 'GitHub 仓库',
    en: () => 'GITHUB REPOSITORY',
    ja: () => 'GitHub リポジトリ',
  },
  aboutStack: {
    zh: () => '更新日志',
    en: () => 'CHANGELOG',
    ja: () => '更新履歴',
  },
  aboutChange1: {
    zh: () => '单进程入口：FastAPI 托管网页与 API',
    en: () => 'One process serves the web UI and API',
    ja: () => '単一プロセスで Web UI と API を提供',
  },
  aboutChange2: {
    zh: () => '新增 Linux / Windows / macOS 发布包构建流程',
    en: () => 'Release builds for Linux, Windows and macOS',
    ja: () => 'Linux / Windows / macOS 向けビルドを追加',
  },
  aboutChange3: {
    zh: () => 'Linux 安装改为下载发布包并校验 SHA256',
    en: () => 'Linux installer downloads releases with SHA256 verification',
    ja: () => 'Linux インストーラーに SHA256 検証を追加',
  },
  aboutCapabilities: {
    zh: () => '核心能力',
    en: () => 'CAPABILITIES',
    ja: () => '主な機能',
  },
  aboutCapability1: {
    zh: () => '会话认证与密码哈希',
    en: () => 'Session authentication with password hashing',
    ja: () => 'セッション認証とパスワードハッシュ',
  },
  aboutCapability2: {
    zh: () => '实例注册、状态与端口管理',
    en: () => 'Instance registration, status and port management',
    ja: () => 'インスタンス登録・状態・ポート管理',
  },
  aboutCapability3: {
    zh: () => 'Java / 基岩 / MCDR 核心与版本选择',
    en: () => 'Java, Bedrock and MCDR core/version selection',
    ja: () => 'Java / Bedrock / MCDR コアとバージョン選択',
  },
  aboutCapability4: {
    zh: () => 'zip / tar.gz 上传与安全解压',
    en: () => 'zip / tar.gz uploads with safe extraction',
    ja: () => 'zip / tar.gz のアップロードと安全な展開',
  },
  aboutCapability5: {
    zh: () => 'Java 版本与 JVM 内存配置',
    en: () => 'Java version and JVM memory configuration',
    ja: () => 'Java バージョンと JVM メモリ設定',
  },
  aboutCapability6: {
    zh: () => '官方资源与镜像源下载',
    en: () => 'Official resources and mirror downloads',
    ja: () => '公式リソースとミラーからのダウンロード',
  },
  aboutDeployment: {
    zh: () => '部署与运行',
    en: () => 'DEPLOYMENT',
    ja: () => 'デプロイと運用',
  },
  aboutProcess: {
    zh: () => 'systemd · Java 子进程',
    en: () => 'systemd · Java subprocess',
    ja: () => 'systemd · Java プロセス',
  },
  aboutHosting: {
    zh: () => '自托管',
    en: () => 'Self-hosted',
    ja: () => 'セルフホスト',
  },
}
export const aboutMessages: Record<string, Record<Locale, () => string>> = text
