type Locale = 'zh' | 'en' | 'ja'
const text: Record<string, Record<Locale, () => string>> = {
  deploy_quick_deploy: {
    zh: () => '快速部署',
    en: () => 'QUICK DEPLOY',
    ja: () => 'クイックデプロイ',
  },
  deploy_pick_a_core_version_and_build_online: {
    zh: () => '在线选择核心、版本与构建',
    en: () => 'Pick a core, version and build online',
    ja: () => 'コア・バージョン・ビルドをオンラインで選択',
  },
  deploy_bedrock: {
    zh: () => '基岩版',
    en: () => 'BEDROCK',
    ja: () => 'Bedrock 版',
  },
  deploy_deploy_bedrock_dedicated_server: {
    zh: () => '部署 Bedrock Dedicated Server',
    en: () => 'Deploy Bedrock Dedicated Server',
    ja: () => 'Bedrock 専用サーバーをデプロイ',
  },
  deploy_upload_modpack: {
    zh: () => '上传整合包',
    en: () => 'UPLOAD MODPACK',
    ja: () => 'Modpack をアップロード',
  },
  deploy_upload_extract_and_auto_detect_the_server_core: {
    zh: () => '上传、解压并自动检测服务端核心',
    en: () => 'Upload, extract and auto-detect the server core',
    ja: () => 'アップロード・展開してコアを自動検出',
  },
  deploy_manage_the_minecraft_server_with_python: {
    zh: () => '使用 Python 管理 Minecraft 服务端',
    en: () => 'Manage the Minecraft server with Python',
    ja: () => 'Python で Minecraft サーバーを管理',
  },
  deploy_basic_info: {
    zh: () => '基本信息',
    en: () => 'BASIC INFO',
    ja: () => '基本情報',
  },
  deploy_core_files: {
    zh: () => '核心文件',
    en: () => 'CORE FILES',
    ja: () => 'コアファイル',
  },
  deploy_server_version: {
    zh: () => '服务端版本',
    en: () => 'SERVER VERSION',
    ja: () => 'サーバーバージョン',
  },
  deploy_upload_modpack_2: {
    zh: () => '上传整合包',
    en: () => 'UPLOAD MODPACK',
    ja: () => 'Modpack アップロード',
  },
  deploy_core_config: {
    zh: () => '核心配置',
    en: () => 'CORE CONFIG',
    ja: () => 'コア設定',
  },
  deploy_environment: {
    zh: () => '环境与设置',
    en: () => 'ENVIRONMENT',
    ja: () => '環境と設定',
  },
  deploy_confirmation: {
    zh: () => '确认信息',
    en: () => 'CONFIRMATION',
    ja: () => '確認',
  },
  deploy_deploy: {
    zh: () => '执行部署',
    en: () => 'DEPLOY',
    ja: () => 'デプロイ実行',
  },
  deploy_result: {
    zh: () => '完成结果',
    en: () => 'RESULT',
    ja: () => '完了',
  },
  deploy_only_zip_tar_gz_or_tgz_modpacks_are_supported: {
    zh: () => '仅支持 .zip、.tar.gz 或 .tgz 整合包。',
    en: () => 'Only .zip, .tar.gz or .tgz modpacks are supported.',
    ja: () => '.zip、.tar.gz、.tgz の Modpack のみ対応しています。',
  },
  deploy_select_one_modpack_at_a_time: {
    zh: () => '每次请选择一个整合包。',
    en: () => 'Select one modpack at a time.',
    ja: () => '一度に選択できる Modpack は 1 つです。',
  },
  deploy_no_launchable_core_found_in_the_modpack: {
    zh: () => '整合包中未找到可启动核心。',
    en: () => 'No launchable core found in the modpack.',
    ja: () => 'Modpack 内に起動可能なコアが見つかりません。',
  },
  deploy_could_not_analyze_the_modpack: {
    zh: () => '整合包分析失败。',
    en: () => 'Could not analyze the modpack.',
    ja: () => 'Modpack の解析に失敗しました。',
  },
  deploy_preparing_deployment: {
    zh: () => '准备部署...',
    en: () => 'Preparing deployment…',
    ja: () => 'デプロイを準備中…',
  },
  deploy_uploading_and_validating_the_modpack_the_instanc: {
    zh: () => '正在上传并校验整合包，完成后创建实例...',
    en: () => 'Uploading and validating the modpack; the instance is created afterwards…',
    ja: () => 'Modpack をアップロード・検証中。完了後にインスタンスを作成します…',
  },
  deploy_modpack_imported_and_instance_created_start_it_m: {
    zh: () => '整合包已导入，实例已创建，可手动启动',
    en: () => 'Modpack imported and instance created; start it manually',
    ja: () => 'Modpack を取り込み、インスタンスを作成しました。手動で起動してください',
  },
  deploy_deployment_complete: {
    zh: () => '部署完成！',
    en: () => 'Deployment complete!',
    ja: () => 'デプロイ完了！',
  },
  deploy_deployment_progress_connection_lost_check_the_ba: {
    zh: () => '部署进度连接中断，请检查后端及实例状态后再重试。',
    en: () => 'Deployment progress connection lost. Check the backend and instance status, then retry.',
    ja: () => 'デプロイ進捗の接続が切れました。バックエンドとインスタンスの状態を確認して再試行してください。',
  },
  deploy_deployment_failed: {
    zh: () => '部署失败。',
    en: () => 'Deployment failed.',
    ja: () => 'デプロイに失敗しました。',
  },
  deploy_complete_the_current_step_first: {
    zh: () => '请先完成当前步骤。',
    en: () => 'Complete the current step first.',
    ja: () => '先に現在のステップを完了してください。',
  },
  deploy_choose_a_mode: {
    zh: () => '选择开服模式',
    en: () => 'CHOOSE A MODE',
    ja: () => '開服モードを選択',
  },
  deploy_new_instance: {
    zh: () => '新建实例',
    en: () => 'NEW INSTANCE',
    ja: () => '新規インスタンス',
  },
  deploy_select_mode: {
    zh: () => '选择模式',
    en: () => 'SELECT MODE',
    ja: () => 'モードを選択',
  },
  deploy_instance_created: {
    zh: () => '实例已创建',
    en: () => 'INSTANCE CREATED',
    ja: () => 'インスタンスを作成しました',
  },
  deploy_the_server_was_written_to_an_isolated_instance_d: {
    zh: () => '服务端已写入独立实例目录，可以进入控制台。',
    en: () => 'The server was written to an isolated instance directory. You can open the console now.',
    ja: () => 'サーバーを専用ディレクトリに書き込みました。コンソールを開けます。',
  },
  deploy_back_to_instances: {
    zh: () => '返回实例列表',
    en: () => 'BACK TO INSTANCES',
    ja: () => 'インスタンス一覧へ',
  },
  deploy_auto_extraction_path_safety_checks_and_core_dete: {
    zh: () => '支持自动解压、路径安全校验和核心检测。',
    en: () => 'Auto-extraction, path safety checks and core detection.',
    ja: () => '自動展開・パス安全検査・コア検出に対応。',
  },
  deploy_drop_a_file_here_or_click_to_choose_zip_tar_gz_t: {
    zh: () => '拖放文件到此处，或点击选择 ZIP / TAR.GZ / TGZ',
    en: () => 'Drop a file here, or click to choose ZIP / TAR.GZ / TGZ',
    ja: () => 'ここにファイルをドロップ、またはクリックして ZIP / TAR.GZ / TGZ を選択',
  },
  deploy_up_to: {
    zh: () => '最大',
    en: () => 'Up to',
    ja: () => '最大',
  },
  deploy_instance_basics: {
    zh: () => '实例基本信息',
    en: () => 'INSTANCE BASICS',
    ja: () => 'インスタンス基本情報',
  },
  deploy_creates_an_instance_local_python_environment_for: {
    zh: () => '将创建实例专用 Python 环境安装 MCDReforged，插件独立存放在 mcdr_plugins；不会改动面板 Python 依赖。',
    en: () =>
      'Creates an instance-local Python environment for MCDReforged; plugins live in mcdr_plugins and the panel Python dependencies are untouched.',
    ja: () =>
      'インスタンス専用の Python 環境に MCDReforged を導入します。プラグインは mcdr_plugins に保存され、パネルの Python 依存には影響しません。',
  },
  deploy_native_bds_does_not_need_java_the_memory_value_i: {
    zh: () => '原生 BDS 不需要 Java；内存值仅作为监测预算，不会伪装成 JVM 内存限制。',
    en: () => 'Native BDS does not need Java; the memory value is only a monitoring budget, not a JVM limit.',
    ja: () => 'ネイティブ BDS に Java は不要です。メモリ値は監視用の目安で、JVM の制限ではありません。',
  },
  deploy_ipv6_udp_port: {
    zh: () => 'IPv6 UDP 端口',
    en: () => 'IPv6 UDP PORT',
    ja: () => 'IPv6 UDP ポート',
  },
  deploy_instance_name: {
    zh: () => '实例名称',
    en: () => 'INSTANCE NAME',
    ja: () => 'インスタンス名',
  },
  deploy_server_port: {
    zh: () => '服务端口',
    en: () => 'SERVER PORT',
    ja: () => 'サーバーポート',
  },
  deploy_official_bedrock_server: {
    zh: () => '基岩版官方服务端',
    en: () => 'OFFICIAL BEDROCK SERVER',
    ja: () => '公式 Bedrock サーバー',
  },
  deploy_fetches_the_supported_stable_release_from_mojang: {
    zh: () =>
      '从 Mojang 官方目录获取本机适用的正式版。需要 Windows x64 或 Ubuntu 22.04+ x64；客户端使用 UDP 端口连接。',
    en: () =>
      'Fetches the supported stable release from Mojang. Requires Windows x64 or Ubuntu 22.04+ x64; clients connect over UDP.',
    ja: () =>
      'Mojang 公式カタログから対応する正式版を取得します。Windows x64 または Ubuntu 22.04+ x64 が必要です。クライアントは UDP で接続します。',
  },
  deploy_loading_official_versions: {
    zh: () => '正在读取官方版本…',
    en: () => 'Loading official versions…',
    ja: () => '公式バージョンを読み込み中…',
  },
  deploy_refresh_catalog: {
    zh: () => '刷新官方目录',
    en: () => 'REFRESH CATALOG',
    ja: () => 'カタログを更新',
  },
  deploy_core_detection: {
    zh: () => '核心检测结果',
    en: () => 'CORE DETECTION',
    ja: () => 'コア検出結果',
  },
  deploy_found: {
    zh: () => '已发现',
    en: () => 'Found',
    ja: () => '',
  },
  deploy_candidate_cores: {
    zh: () => '个候选核心。',
    en: () => 'candidate cores.',
    ja: () => '件の候補コア。',
  },
  deploy_environment_settings: {
    zh: () => '环境与设置',
    en: () => 'ENVIRONMENT & SETTINGS',
    ja: () => '環境と設定',
  },
  deploy_runs_the_native_official_bds_no_java_needed_memo: {
    zh: () => '运行官方原生 BDS，不需要 Java；内存仅作为监测预算。',
    en: () => 'Runs the native official BDS; no Java needed. Memory is only a monitoring budget.',
    ja: () => 'ネイティブ公式 BDS を実行します。Java は不要です。メモリは監視用の目安です。',
  },
  deploy_runs_mcdr_in_an_instance_local_python_environmen: {
    zh: () => '使用实例专用 Python 环境运行 MCDR，并由它启动所选 Java 核心。',
    en: () => 'Runs MCDR in an instance-local Python environment, which launches the selected Java core.',
    ja: () => 'インスタンス専用の Python 環境で MCDR を実行し、選択した Java コアを起動します。',
  },
  deploy_the_host_environment_is_checked_a_setup_hint_app: {
    zh: () => '系统将检测当前主机环境；缺少 Java 时会返回安装提示。',
    en: () => 'The host environment is checked; a setup hint appears if Java is missing.',
    ja: () => 'ホスト環境を確認します。Java が無い場合は導入のヒントを表示します。',
  },
  deploy_agree: {
    zh: () => '同意',
    en: () => 'Agree',
    ja: () => '同意',
  },
  deploy_java_version: {
    zh: () => 'Java 版本',
    en: () => 'Java version',
    ja: () => 'Java バージョン',
  },
  deploy_memory_mb: {
    zh: () => '内存（MB）',
    en: () => 'MEMORY (MB)',
    ja: () => 'メモリ（MB）',
  },
  deploy_confirm_deployment: {
    zh: () => '确认部署信息',
    en: () => 'CONFIRM DEPLOYMENT',
    ja: () => 'デプロイ内容の確認',
  },
  deploy_modpack: {
    zh: () => '整合包：',
    en: () => 'Modpack: ',
    ja: () => 'Modpack：',
  },
  deploy_core: {
    zh: () => '核心',
    en: () => 'CORE',
    ja: () => 'コア',
  },
  deploy_game_version: {
    zh: () => '游戏版本',
    en: () => 'GAME VERSION',
    ja: () => 'ゲームバージョン',
  },
  deploy_build: {
    zh: () => '核心构建',
    en: () => 'BUILD',
    ja: () => 'ビルド',
  },
  deploy_memory: {
    zh: () => '内存',
    en: () => 'MEMORY',
    ja: () => 'メモリ',
  },
  deploy_back: {
    zh: () => '上一步',
    en: () => 'BACK',
    ja: () => '戻る',
  },
  deploy_working: {
    zh: () => '处理中…',
    en: () => 'WORKING…',
    ja: () => '処理中…',
  },
  deploy_confirm_deploy: {
    zh: () => '确认并部署',
    en: () => 'CONFIRM & DEPLOY',
    ja: () => '確認してデプロイ',
  },
  deploy_next: {
    zh: () => '下一步',
    en: () => 'NEXT',
    ja: () => '次へ',
  },
  deploy_open_console: {
    zh: () => '进入控制台',
    en: () => 'OPEN CONSOLE',
    ja: () => 'コンソールへ',
  },
  deploy_failed_to_load_versions: {
    zh: () => '版本加载失败',
    en: () => 'Failed to load versions',
    ja: () => 'バージョンの読み込みに失敗しました',
  },
  deploy_create_instance_directory: {
    zh: () => '创建实例目录',
    en: () => 'Create instance directory',
    ja: () => 'インスタンスディレクトリを作成',
  },
  deploy_download_java_runtime: {
    zh: () => '下载 Java 环境',
    en: () => 'Download Java runtime',
    ja: () => 'Java ランタイムをダウンロード',
  },
  deploy_download_core_files: {
    zh: () => '下载核心文件',
    en: () => 'Download core files',
    ja: () => 'コアファイルをダウンロード',
  },
  deploy_generate_configuration: {
    zh: () => '生成配置文件',
    en: () => 'Generate configuration',
    ja: () => '設定ファイルを生成',
  },
  deploy_start_the_server: {
    zh: () => '启动服务器',
    en: () => 'Start the server',
    ja: () => 'サーバーを起動',
  },
  deploy_java_jvm: {
    zh: () => 'Java / JVM',
    en: () => 'JAVA / JVM',
    ja: () => 'Java / JVM',
  },
  deploy_preparing_deployment_2: {
    zh: () => '准备部署',
    en: () => 'Preparing deployment',
    ja: () => 'デプロイを準備中',
  },
  deploy_deployment_failed_2: {
    zh: () => '部署失败',
    en: () => 'Deployment failed',
    ja: () => 'デプロイに失敗しました',
  },
  deploy_back_2: {
    zh: () => '返回',
    en: () => 'BACK',
    ja: () => '戻る',
  },
  deploy_set_the_instance_name_and_network_port: {
    zh: () => '创建实例名称与网络端口。',
    en: () => 'Set the instance name and network port.',
    ja: () => 'インスタンス名とネットワークポートを指定します。',
  },
  deploy_server_port_2: {
    zh: () => '服务端端口',
    en: () => 'SERVER PORT',
    ja: () => 'サーバーポート',
  },
  deploy_the_name_may_only_contain_letters_digits_and_hyp: {
    zh: () => '名称只能包含英文、数字和连字符。',
    en: () => 'The name may only contain letters, digits and hyphens.',
    ja: () => '名前は英数字とハイフンのみ使用できます。',
  },
  deploy_selecting_a_core_does_not_download_it_now_it_hap: {
    zh: () => '选择核心后不会立即下载，确认后继续下一步。',
    en: () => 'Selecting a core does not download it now; it happens after confirmation.',
    ja: () => 'コアを選んでもすぐにはダウンロードされません。確認後に実行されます。',
  },
  deploy_choose_a_server_core: {
    zh: () => '选择服务端核心',
    en: () => 'CHOOSE A SERVER CORE',
    ja: () => 'サーバーコアを選択',
  },
  deploy_selected: {
    zh: () => '已选择：',
    en: () => 'Selected: ',
    ja: () => '選択中：',
  },
  deploy_java_jvm_settings: {
    zh: () => 'Java 环境与 JVM 设置',
    en: () => 'JAVA & JVM SETTINGS',
    ja: () => 'Java と JVM の設定',
  },
  deploy_java: {
    zh: () => '系统已自动匹配',
    en: () => 'Java',
    ja: () => 'Java',
  },
  deploy_has_been_matched_automatically: {
    zh: () => '环境。',
    en: () => 'has been matched automatically.',
    ja: () => 'が自動的に選択されました。',
  },
  deploy_memory_2: {
    zh: () => '内存分配',
    en: () => 'MEMORY',
    ja: () => 'メモリ割り当て',
  },
  deploy_use_aikar_s_flags: {
    zh: () => "使用 Aikar's flags",
    en: () => "Use Aikar's flags",
    ja: () => "Aikar's flags を使用",
  },
  deploy_port: {
    zh: () => '端口',
    en: () => 'PORT',
    ja: () => 'ポート',
  },
  deploy_version: {
    zh: () => '版本',
    en: () => 'VERSION',
    ja: () => 'バージョン',
  },
  deploy_created_successfully: {
    zh: () => '创建成功！',
    en: () => 'Created successfully!',
    ja: () => '作成に成功しました！',
  },
  deploy_deploying: {
    zh: () => '正在执行部署',
    en: () => 'Deploying',
    ja: () => 'デプロイ実行中',
  },
  deploy_open_instance_list: {
    zh: () => '进入实例列表',
    en: () => 'OPEN INSTANCE LIST',
    ja: () => 'インスタンス一覧へ',
  },
  deploy_confirm_create: {
    zh: () => '确认并创建',
    en: () => 'CONFIRM & CREATE',
    ja: () => '確認して作成',
  },
  deploy_server_core: {
    zh: () => '服务端核心',
    en: () => 'Server core',
    ja: () => 'サーバーコア',
  },
  deploy_high_performance_spigot_fork: {
    zh: () => '高性能 Spigot 分支',
    en: () => 'High-performance Spigot fork',
    ja: () => '高性能 Spigot フォーク',
  },
  deploy_highly_customizable_paper_fork: {
    zh: () => 'Paper 的高可定制分支',
    en: () => 'Highly customizable Paper fork',
    ja: () => '高いカスタマイズ性の Paper フォーク',
  },
  deploy_region_parallel_server: {
    zh: () => '面向区域并行的服务端',
    en: () => 'Region-parallel server',
    ja: () => 'リージョン並列サーバー',
  },
  deploy_lightweight_flexible_mod_loader: {
    zh: () => '轻量灵活的模组加载器',
    en: () => 'Lightweight, flexible mod loader',
    ja: () => '軽量で柔軟な MOD ローダー',
  },
  deploy_classic_minecraft_mod_platform: {
    zh: () => '经典 Minecraft 模组平台',
    en: () => 'Classic Minecraft mod platform',
    ja: () => '定番の Minecraft MOD プラットフォーム',
  },
  deploy_official_vanilla_minecraft_server: {
    zh: () => '官方原版 Minecraft 服务端',
    en: () => 'Official vanilla Minecraft server',
    ja: () => '公式バニラ Minecraft サーバー',
  },
  deploy_modern_high_performance_proxy: {
    zh: () => '现代高性能代理服务端',
    en: () => 'Modern high-performance proxy',
    ja: () => 'モダンで高性能なプロキシ',
  },
  deploy_choose_game_version: {
    zh: () => '选择游戏版本',
    en: () => 'CHOOSE GAME VERSION',
    ja: () => 'ゲームバージョンを選択',
  },
  deploy_choose_build: {
    zh: () => '选择构建版本',
    en: () => 'CHOOSE BUILD',
    ja: () => 'ビルドを選択',
  },
  deploy_close: {
    zh: () => '关闭',
    en: () => 'Close',
    ja: () => '閉じる',
  },
  deploy_choose_a_minecraft_game_version_to_continue: {
    zh: () => '选择一个 Minecraft 游戏版本以继续。',
    en: () => 'Choose a Minecraft game version to continue.',
    ja: () => '続行する Minecraft のバージョンを選択してください。',
  },
  deploy_loading_latest_version_data: {
    zh: () => '正在获取最新版本数据...',
    en: () => 'Loading latest version data…',
    ja: () => '最新バージョンを読み込み中…',
  },
  deploy_no_versions_available: {
    zh: () => '暂无可用版本',
    en: () => 'No versions available',
    ja: () => '利用可能なバージョンがありません',
  },
  deploy_back_to_versions: {
    zh: () => '返回游戏版本',
    en: () => 'BACK TO VERSIONS',
    ja: () => 'バージョンに戻る',
  },
  deploy_available_builds: {
    zh: () => '的可用构建版本。',
    en: () => 'available builds.',
    ja: () => 'の利用可能なビルド。',
  },
  deploy_hybrid_recommended: {
    zh: () => '混合端（推荐）',
    en: () => 'Hybrid (recommended)',
    ja: () => 'ハイブリッド（推奨）',
  },
  deploy_hybrid: {
    zh: () => '混合端',
    en: () => 'Hybrid',
    ja: () => 'ハイブリッド',
  },
  deploy_lightweight_mod_loader: {
    zh: () => '轻量模组加载器',
    en: () => 'Lightweight mod loader',
    ja: () => '軽量 MOD ローダー',
  },
  deploy_classic_mod_platform: {
    zh: () => '经典模组平台',
    en: () => 'Classic mod platform',
    ja: () => '定番 MOD プラットフォーム',
  },
  deploy_next_gen_mod_ecosystem: {
    zh: () => '新一代模组生态',
    en: () => 'Next-gen mod ecosystem',
    ja: () => '次世代 MOD エコシステム',
  },
  deploy_fabric_derived_loader: {
    zh: () => 'Fabric 衍生加载器',
    en: () => 'Fabric-derived loader',
    ja: () => 'Fabric 派生ローダー',
  },
  deploy_proxy_server: {
    zh: () => '代理服务端',
    en: () => 'Proxy server',
    ja: () => 'プロキシサーバー',
  },
  deploy_modern_proxy_server: {
    zh: () => '现代代理服务端',
    en: () => 'Modern proxy server',
    ja: () => 'モダンなプロキシ',
  },
  deploy_multi_threaded_region_parallelism: {
    zh: () => '多线程区域并行',
    en: () => 'Multi-threaded region parallelism',
    ja: () => 'マルチスレッドのリージョン並列',
  },
  deploy_paper_derived_server: {
    zh: () => 'Paper 衍生服务端',
    en: () => 'Paper-derived server',
    ja: () => 'Paper 派生サーバー',
  },
  deploy_high_performance_plugin_server_recommended: {
    zh: () => '高性能插件服务端（推荐）',
    en: () => 'High-performance plugin server (recommended)',
    ja: () => '高性能プラグインサーバー（推奨）',
  },
  deploy_highly_customizable_server: {
    zh: () => '高可定制服务端',
    en: () => 'Highly customizable server',
    ja: () => '高いカスタマイズ性',
  },
  deploy_classic_plugin_server: {
    zh: () => '经典插件服务端',
    en: () => 'Classic plugin server',
    ja: () => '定番プラグインサーバー',
  },
  deploy_sponge_plugin_server: {
    zh: () => 'Sponge 插件服务端',
    en: () => 'Sponge plugin server',
    ja: () => 'Sponge プラグインサーバー',
  },
  deploy_bedrock_server: {
    zh: () => '基岩版服务端',
    en: () => 'Bedrock server',
    ja: () => 'Bedrock サーバー',
  },
  deploy_official_vanilla_server: {
    zh: () => '官方原版服务端',
    en: () => 'Official vanilla server',
    ja: () => '公式バニラサーバー',
  },
  deploy_forge_hybrid_ecosystem: {
    zh: () => 'Forge 混合生态',
    en: () => 'Forge hybrid ecosystem',
    ja: () => 'Forge ハイブリッド',
  },
  deploy_neoforge_hybrid_ecosystem: {
    zh: () => 'NeoForge 混合生态',
    en: () => 'NeoForge hybrid ecosystem',
    ja: () => 'NeoForge ハイブリッド',
  },
  deploy_failed_to_load_builds: {
    zh: () => '构建加载失败',
    en: () => 'Failed to load builds',
    ja: () => 'ビルドの読み込みに失敗しました',
  },

  deploy_category_plugin: {
    zh: () => '插件服务端',
    en: () => 'PLUGIN',
    ja: () => 'プラグイン',
  },
  deploy_category_modded: {
    zh: () => '模组服务端',
    en: () => 'MODDED',
    ja: () => 'Mod',
  },
  deploy_category_proxy: {
    zh: () => '代理服务端',
    en: () => 'PROXY',
    ja: () => 'プロキシ',
  },
  deploy_category_bedrock: {
    zh: () => '基岩服务端',
    en: () => 'BEDROCK',
    ja: () => 'Bedrock',
  },
  deploy_category_vanilla: {
    zh: () => '原版服务端',
    en: () => 'VANILLA',
    ja: () => 'バニラ',
  },
  deploy_category_hybrid: {
    zh: () => '混合服务端',
    en: () => 'HYBRID',
    ja: () => 'ハイブリッド',
  },
  deploy_modpack_too_large: {
    zh: () => '整合包不能超过 {size}MB。',
    en: () => 'The modpack must not exceed {size}MB.',
    ja: () => 'Modpack は {size}MB を超えられません。',
  },
}
export const deployMessages: Record<string, Record<Locale, () => string>> = text
