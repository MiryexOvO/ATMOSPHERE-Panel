type Locale = 'zh' | 'en' | 'ja'
const text: Record<string, Record<Locale, () => string>> = {
  msg_certificate_validated_and_saved: {
    zh: () => '证书已验证并保存',
    en: () => 'Certificate validated and saved',
    ja: () => '証明書を検証して保存しました',
  },
  msg_software_update: {
    zh: () => '软件更新',
    en: () => 'SOFTWARE UPDATE',
    ja: () => 'ソフトウェア更新',
  },
  msg_processing: {
    zh: () => '处理中…',
    en: () => 'PROCESSING…',
    ja: () => '処理中…',
  },
  msg_check_for_updates: {
    zh: () => '检查更新',
    en: () => 'CHECK FOR UPDATES',
    ja: () => '更新を確認',
  },
  msg_auto_download_releases_hourly: {
    zh: () => '发现正式版本后自动下载（每小时检查）',
    en: () => 'AUTO-DOWNLOAD RELEASES (HOURLY)',
    ja: () => '正式版を自動ダウンロード（毎時確認）',
  },
  msg_auto_download: {
    zh: () => '自动下载',
    en: () => 'AUTO-DOWNLOAD',
    ja: () => '自動ダウンロード',
  },
  msg_new_version_available: {
    zh: () => '发现新版本',
    en: () => 'NEW VERSION AVAILABLE',
    ja: () => '新しいバージョンがあります',
  },
  msg_up_to_date: {
    zh: () => '当前已是最新版本',
    en: () => 'UP TO DATE',
    ja: () => '最新版です',
  },
  msg_download_update: {
    zh: () => '下载新版本',
    en: () => 'DOWNLOAD UPDATE',
    ja: () => '更新をダウンロード',
  },
  msg_release_page: {
    zh: () => '查看发布页',
    en: () => 'RELEASE PAGE',
    ja: () => 'リリースページ',
  },
  msg_save_downloaded_package: {
    zh: () => '保存已下载的更新包',
    en: () => 'SAVE DOWNLOADED PACKAGE',
    ja: () => 'ダウンロード済みパッケージを保存',
  },
  msg_update_packages_are_stored_in_the_panel_data: {
    zh: () => '更新包下载到面板数据目录。不会在游戏运行时自动覆盖程序。',
    en: () =>
      'Update packages are stored in the panel data directory. Running server files are never overwritten automatically.',
    ja: () => '更新パッケージはデータ領域に保存します。稼働中のファイルは自動上書きしません。',
  },
  msg_https_access: {
    zh: () => 'HTTPS 加密访问',
    en: () => 'HTTPS ACCESS',
    ja: () => 'HTTPS アクセス',
  },
  msg_enable_https: {
    zh: () => '开启 HTTPS',
    en: () => 'ENABLE HTTPS',
    ja: () => 'HTTPS を有効化',
  },
  msg_self_signed_certificate: {
    zh: () => '自动生成自签证书',
    en: () => 'SELF-SIGNED CERTIFICATE',
    ja: () => '自己署名証明書',
  },
  msg_https_port: {
    zh: () => 'HTTPS 入口端口',
    en: () => 'HTTPS PORT',
    ja: () => 'HTTPS ポート',
  },
  msg_local_frontend_port: {
    zh: () => '本机前端端口',
    en: () => 'LOCAL FRONTEND PORT',
    ja: () => 'ローカルフロントエンドポート',
  },
  msg_after_saving_use_the_https_entry_browsers_re: {
    zh: () => '保存后使用新入口访问；自签证书首次访问需要浏览器确认，公网域名请上传正式证书。',
    en: () =>
      'After saving, use the HTTPS entry. Browsers require approval for self-signed certificates. Upload a trusted certificate for a public domain.',
    ja: () =>
      '保存後に HTTPS 入口へアクセス。自己署名証明書はブラウザの確認が必要です。公開ドメインでは正式な証明書をご利用ください。',
  },
  msg_disable_and_save_https_before_uploading_pem_: {
    zh: () => '先关闭并保存 HTTPS，再上传 PEM 证书与私钥。',
    en: () => 'Disable and save HTTPS before uploading PEM certificate and key.',
    ja: () => 'HTTPS を無効化して保存後、PEM 証明書と秘密鍵をアップロード。',
  },
  msg_validate_save_certificate: {
    zh: () => '验证并保存证书',
    en: () => 'VALIDATE & SAVE CERTIFICATE',
    ja: () => '証明書を検証・保存',
  },
  msg_view: {
    zh: () => '查看状态',
    en: () => 'VIEW',
    ja: () => '状態閲覧',
  },
  msg_console: {
    zh: () => '控制台日志',
    en: () => 'CONSOLE',
    ja: () => 'ログ',
  },
  msg_power: {
    zh: () => '电源控制',
    en: () => 'POWER',
    ja: () => '電源',
  },
  msg_command: {
    zh: () => '发送命令',
    en: () => 'COMMAND',
    ja: () => 'コマンド',
  },
  msg_files_addons: {
    zh: () => '文件与扩展',
    en: () => 'FILES & ADDONS',
    ja: () => 'ファイル',
  },
  msg_backups: {
    zh: () => '备份',
    en: () => 'BACKUPS',
    ja: () => 'バックアップ',
  },
  msg_settings: {
    zh: () => '实例配置',
    en: () => 'SETTINGS',
    ja: () => '設定',
  },
  msg_players: {
    zh: () => '玩家管理',
    en: () => 'PLAYERS',
    ja: () => 'プレイヤー',
  },
  msg_schedules: {
    zh: () => '定时任务',
    en: () => 'SCHEDULES',
    ja: () => '定期タスク',
  },
  msg_delete_server: {
    zh: () => '删除实例',
    en: () => 'DELETE SERVER',
    ja: () => 'サーバー削除',
  },
  msg_administrators_manage_all_resources_operator: {
    zh: () => '管理员管理全站；操作员仅管理分配的实例及所选能力；只读账户不能执行写入操作。',
    en: () =>
      'Administrators manage all resources. Operators receive assigned servers and capabilities. Viewers cannot modify resources.',
    ja: () => '管理者は全体を管理。オペレーターは割り当てられたインスタンスと権限のみ。閲覧者は変更できません。',
  },
  msg_search_users: {
    zh: () => '搜索用户名或昵称',
    en: () => 'SEARCH USERS',
    ja: () => 'ユーザーを検索',
  },
  msg_last_login: {
    zh: () => '最后登录',
    en: () => 'LAST LOGIN',
    ja: () => '最終ログイン',
  },
  msg_current_account: {
    zh: () => '当前账户',
    en: () => 'CURRENT ACCOUNT',
    ja: () => '現在のアカウント',
  },
  msg_display_name: {
    zh: () => '昵称',
    en: () => 'DISPLAY NAME',
    ja: () => '表示名',
  },
  msg_assigned_servers_and_permissions: {
    zh: () => '分配实例与操作权限（未分配不可访问）',
    en: () => 'ASSIGNED SERVERS AND PERMISSIONS',
    ja: () => 'インスタンスと操作権限',
  },
  msg_apply_to_selected_servers: {
    zh: () => '确认操作选中的实例？',
    en: () => 'Apply to selected servers?',
    ja: () => '選択したサーバーに実行しますか？',
  },
  msg_multi_server_operations: {
    zh: () => '多实例批量操作',
    en: () => 'MULTI-SERVER OPERATIONS',
    ja: () => '複数サーバー操作',
  },
  msg_restart_selected: {
    zh: () => '一键重启',
    en: () => 'RESTART SELECTED',
    ja: () => '一括再起動',
  },
  msg_broadcast_command: {
    zh: () => '同步命令',
    en: () => 'BROADCAST COMMAND',
    ja: () => 'コマンド同期',
  },
  msg_start_selected: {
    zh: () => '批量启动',
    en: () => 'START SELECTED',
    ja: () => '一括起動',
  },
  msg_stop_selected: {
    zh: () => '批量停止',
    en: () => 'STOP SELECTED',
    ja: () => '一括停止',
  },
  msg_single_server_command: {
    zh: () => '单行服务器命令',
    en: () => 'SINGLE SERVER COMMAND',
    ja: () => 'サーバーコマンド',
  },
  msg_running: {
    zh: () => '执行中…',
    en: () => 'RUNNING…',
    ja: () => '実行中…',
  },
  msg_execute: {
    zh: () => '执行',
    en: () => 'EXECUTE',
    ja: () => '実行',
  },
  msg_new_network_sign_in_detected_verify_this_act: {
    zh: () => '检测到新网络登录，请检查是否为本人操作：',
    en: () => 'New-network sign-in detected. Verify this activity:',
    ja: () => '新しいネットワークからのログインを確認してください：',
  },
  msg_dismiss: {
    zh: () => '已知晓',
    en: () => 'DISMISS',
    ja: () => '確認済み',
  },
  msg_two_factor_settings_saved: {
    zh: () => '二步验证设置已保存',
    en: () => 'Two-factor settings saved',
    ja: () => '二段階認証の設定を保存しました',
  },
  msg_login_security: {
    zh: () => '登录验证与提醒',
    en: () => 'LOGIN SECURITY',
    ja: () => 'ログイン保護',
  },
  msg_use_an_authenticator_for_six_digit_codes_new: {
    zh: () => '使用认证器生成六位验证码。新网络登录会显示提醒；仅比较网络来源，不推测地理位置。请妥善保存验证器密钥。',
    en: () =>
      'Use an authenticator for six-digit codes. New-network sign-ins are flagged without inferring location. Keep your authenticator secret safe.',
    ja: () =>
      '認証アプリの 6 桁コードを使用。新しいネットワークからのログインを通知します。位置情報の推測は行いません。鍵を安全に保管してください。',
  },
  msg_current_password: {
    zh: () => '当前密码',
    en: () => 'CURRENT PASSWORD',
    ja: () => '現在のパスワード',
  },
  msg_add_this_secret_in_your_authenticator_then_c: {
    zh: () => '在验证器中手动添加以下密钥，再输入验证码确认。',
    en: () => 'Add this secret in your authenticator, then confirm with its code.',
    ja: () => '認証アプリに以下の鍵を登録し、確認コードを入力してください。',
  },
  msg_open_authenticator: {
    zh: () => '打开本机验证器',
    en: () => 'OPEN AUTHENTICATOR',
    ja: () => '認証アプリを開く',
  },
  msg_set_up_two_factor: {
    zh: () => '配置二步验证',
    en: () => 'SET UP TWO-FACTOR',
    ja: () => '二段階認証を設定',
  },
  msg_confirm_enable: {
    zh: () => '确认启用',
    en: () => 'CONFIRM ENABLE',
    ja: () => '有効化を確認',
  },
  msg_disable_two_factor: {
    zh: () => '关闭二步验证',
    en: () => 'DISABLE TWO-FACTOR',
    ja: () => '二段階認証を無効化',
  },
  msg_new_network: {
    zh: () => '新网络登录',
    en: () => 'NEW NETWORK',
    ja: () => '新しいネットワーク',
  },
  msg_send_command: {
    zh: () => '发送命令',
    en: () => 'SEND COMMAND',
    ja: () => 'コマンド送信',
  },
  msg_restart_server: {
    zh: () => '重启实例',
    en: () => 'RESTART SERVER',
    ja: () => '再起動',
  },
  msg_start_server: {
    zh: () => '启动实例',
    en: () => 'START SERVER',
    ja: () => '起動',
  },
  msg_stop_server: {
    zh: () => '停止实例',
    en: () => 'STOP SERVER',
    ja: () => '停止',
  },
  msg_offline_backup: {
    zh: () => '停服一致性备份',
    en: () => 'OFFLINE BACKUP',
    ja: () => '停止中のバックアップ',
  },
  msg_delete_this_task: {
    zh: () => '删除任务？',
    en: () => 'Delete this task?',
    ja: () => 'タスクを削除しますか？',
  },
  msg_run_this_task_now: {
    zh: () => '立即执行此任务？',
    en: () => 'Run this task now?',
    ja: () => '今すぐ実行しますか？',
  },
  msg_global_schedules: {
    zh: () => '全局定时任务',
    en: () => 'GLOBAL SCHEDULES',
    ja: () => 'グローバル定期タスク',
  },
  msg_five_or_six_field_cron_utc_missed_executions: {
    zh: () => '支持五段 / 六段 Cron，执行时区 UTC。后端离线期间错过的任务恢复后只执行一次。',
    en: () => 'Five or six-field Cron, UTC. Missed executions run once when the backend resumes.',
    ja: () => '5・6 フィールド Cron、UTC。停止中の未実行分は復旧時に一度だけ実行。',
  },
  msg_new_task: {
    zh: () => '新增任务',
    en: () => 'NEW TASK',
    ja: () => '新規タスク',
  },
  msg_next_run: {
    zh: () => '下次执行',
    en: () => 'NEXT RUN',
    ja: () => '次回',
  },
  msg_run_now: {
    zh: () => '立即执行',
    en: () => 'RUN NOW',
    ja: () => '今すぐ実行',
  },
  msg_edit: {
    zh: () => '编辑',
    en: () => 'EDIT',
    ja: () => '編集',
  },
  msg_delete: {
    zh: () => '删除',
    en: () => 'DELETE',
    ja: () => '削除',
  },
  msg_no_scheduled_tasks: {
    zh: () => '暂无定时任务',
    en: () => 'NO SCHEDULED TASKS',
    ja: () => '定期タスクはありません',
  },
  msg_scheduled_task: {
    zh: () => '定时任务',
    en: () => 'SCHEDULED TASK',
    ja: () => '定期タスク',
  },
  msg_instance: {
    zh: () => '归属实例',
    en: () => 'INSTANCE',
    ja: () => 'インスタンス',
  },
  msg_task_name: {
    zh: () => '任务名称',
    en: () => 'TASK NAME',
    ja: () => 'タスク名',
  },
  msg_every_30_min: {
    zh: () => '每30分钟',
    en: () => 'EVERY 30 MIN',
    ja: () => '30 分毎',
  },
  msg_daily_04_00_utc: {
    zh: () => '每日04:00 UTC',
    en: () => 'DAILY 04:00 UTC',
    ja: () => '毎日 04:00 UTC',
  },
  msg_console_command: {
    zh: () => '控制台命令',
    en: () => 'CONSOLE COMMAND',
    ja: () => 'コンソールコマンド',
  },
  msg_enable_task: {
    zh: () => '启用任务',
    en: () => 'ENABLE TASK',
    ja: () => 'タスク有効',
  },
  msg_cancel: {
    zh: () => '取消',
    en: () => 'CANCEL',
    ja: () => 'キャンセル',
  },
  msg_save_task: {
    zh: () => '保存配置',
    en: () => 'SAVE TASK',
    ja: () => '保存',
  },
  msg_created: {
    zh: () => '已创建：',
    en: () => 'Created: ',
    ja: () => '作成済み：',
  },
  msg_backup_failed: {
    zh: () => '备份失败',
    en: () => 'Backup failed',
    ja: () => 'バックアップに失敗しました',
  },
  msg_backups_restore: {
    zh: () => '备份与恢复',
    en: () => 'BACKUPS & RESTORE',
    ja: () => 'バックアップと復元',
  },
  msg_working: {
    zh: () => '处理中…',
    en: () => 'WORKING…',
    ja: () => '処理中…',
  },
  msg_create_backup: {
    zh: () => '一键备份',
    en: () => 'CREATE BACKUP',
    ja: () => 'バックアップ作成',
  },
  msg_no_backups_yet: {
    zh: () => '暂无备份记录',
    en: () => 'NO BACKUPS YET',
    ja: () => 'バックアップはありません',
  },
  msg_mod_list: {
    zh: () => '模组列表',
    en: () => 'MOD LIST',
    ja: () => 'MOD 一覧',
  },
  msg_plugin_list: {
    zh: () => '插件列表',
    en: () => 'PLUGIN LIST',
    ja: () => 'プラグイン一覧',
  },
  msg_grant_op: {
    zh: () => '授予 OP',
    en: () => 'GRANT OP',
    ja: () => 'OP を付与',
  },
  msg_revoke_op: {
    zh: () => '取消 OP',
    en: () => 'REVOKE OP',
    ja: () => 'OP を解除',
  },
  msg_kick: {
    zh: () => '踢出',
    en: () => 'KICK',
    ja: () => 'キック',
  },
  msg_ban: {
    zh: () => '封禁',
    en: () => 'BAN',
    ja: () => 'BAN',
  },
  msg_pardon: {
    zh: () => '解封',
    en: () => 'PARDON',
    ja: () => 'BAN 解除',
  },
  msg_add_to_whitelist: {
    zh: () => '加入白名单',
    en: () => 'ADD TO WHITELIST',
    ja: () => 'ホワイトリスト追加',
  },
  msg_remove_from_whitelist: {
    zh: () => '移出白名单',
    en: () => 'REMOVE FROM WHITELIST',
    ja: () => 'ホワイトリスト削除',
  },
  msg_online_players: {
    zh: () => '在线玩家',
    en: () => 'ONLINE PLAYERS',
    ja: () => 'オンラインプレイヤー',
  },
  msg_refresh: {
    zh: () => '刷新',
    en: () => 'REFRESH',
    ja: () => '更新',
  },
  msg_no_online_players: {
    zh: () => '目前没有在线玩家',
    en: () => 'NO ONLINE PLAYERS',
    ja: () => 'オンラインプレイヤーはいません',
  },
  msg_player_action: {
    zh: () => '玩家操作',
    en: () => 'PLAYER ACTION',
    ja: () => 'プレイヤー操作',
  },
  msg_apply_to_selected: {
    zh: () => '执行选中操作',
    en: () => 'APPLY TO SELECTED',
    ja: () => '選択した操作を実行',
  },
  msg_choose_jpg_png_under_10_mb: {
    zh: () => '请选择小于 10 MB 的 JPG / PNG',
    en: () => 'Choose JPG / PNG under 10 MB',
    ja: () => '10 MB 以下の JPG / PNG を選択',
  },
  msg_unable_to_read_image: {
    zh: () => '无法读取图片',
    en: () => 'Unable to read image',
    ja: () => '画像を読み込めません',
  },
  msg_icon_saved_takes_effect_on_start: {
    zh: () => '图标已保存，启动后生效',
    en: () => 'Icon saved; takes effect on start',
    ja: () => 'アイコンを保存しました。起動後に反映されます',
  },
  msg_exporting: {
    zh: () => '正在导出 ',
    en: () => 'EXPORTING ',
    ja: () => 'エクスポート中 ',
  },
  msg_server_exported: {
    zh: () => '服务端已导出',
    en: () => 'Server exported',
    ja: () => 'エクスポート完了',
  },
  msg_server_icon_export: {
    zh: () => '服务器图标与导出',
    en: () => 'SERVER ICON & EXPORT',
    ja: () => 'サーバーアイコンとエクスポート',
  },
  msg_choose_jpg_png: {
    zh: () => '选择 JPG / PNG',
    en: () => 'CHOOSE JPG / PNG',
    ja: () => 'JPG / PNG を選択',
  },
  msg_export_full_server: {
    zh: () => '导出完整服务端',
    en: () => 'EXPORT FULL SERVER',
    ja: () => 'サーバー全体をエクスポート',
  },
  msg_stop_the_server_first_export_includes_worlds: {
    zh: () => '停服后操作。导出包含世界存档、插件、MODS、配置文件与核心。',
    en: () => 'Stop the server first. Export includes worlds, plugins, mods, configuration and core.',
    ja: () => '停止後に操作してください。ワールド、プラグイン、MOD、設定、コアを含みます。',
  },
  msg_zoom: {
    zh: () => '缩放',
    en: () => 'ZOOM',
    ja: () => '拡大',
  },
  msg_save_crop_64_64: {
    zh: () => '保存裁剪 · 64×64',
    en: () => 'SAVE CROP · 64×64',
    ja: () => '切り抜きを保存 · 64×64',
  },
  msg_cpu_is_normalized_by_host_logical_cores_and_: {
    zh: () => 'CPU 按主机逻辑核心数归一化，只统计此实例的进程树；内存相对于实例分配上限。',
    en: () =>
      'CPU is normalized by host logical cores and measures only this instance process tree. Memory is relative to the instance allocation.',
    ja: () =>
      'CPU はホストの論理コア数で正規化し、このインスタンスのプロセス群のみ計測。メモリは割当上限に対する割合です。',
  },
  msg_single_core_equivalent: {
    zh: () => '单核等效',
    en: () => 'SINGLE-CORE EQUIVALENT',
    ja: () => '単一コア換算',
  },
  msg_total_read_write: {
    zh: () => '累计读取 / 写入',
    en: () => 'TOTAL READ / WRITE',
    ja: () => '累積読み取り / 書き込み',
  },
  msg_process_disk_stats_unavailable_on_this_platf: {
    zh: () => '此平台不提供进程磁盘统计',
    en: () => 'PROCESS DISK STATS UNAVAILABLE ON THIS PLATFORM',
    ja: () => 'この環境ではプロセスのディスク統計を取得できません',
  },
  msg_loading_monitor_data: {
    zh: () => '读取监控数据……',
    en: () => 'LOADING MONITOR DATA……',
    ja: () => 'モニターデータを読み込み中……',
  },
  msg_system_start_the_server_before_sending_your_: {
    zh: () => '[系统] 实例已停止，请启动后发送；已输入的命令会保留。',
    en: () => '[SYSTEM] Start the server before sending. Your command is preserved.',
    ja: () => '[SYSTEM] 起動後に送信してください。入力内容は保持されます。',
  },
  msg_failed_to_send_command: {
    zh: () => '指令发送失败',
    en: () => 'Failed to send command',
    ja: () => 'コマンド送信に失敗しました',
  },
  msg_waiting_for_server_logs: {
    zh: () => '等待服务端日志……',
    en: () => 'WAITING FOR SERVER LOGS……',
    ja: () => 'サーバーログを待機中……',
  },
  msg_enter_a_server_command_e_g_say_hello: {
    zh: () => '输入服务器指令，例如 say hello',
    en: () => 'Enter a server command, e.g. say hello',
    ja: () => 'サーバーコマンドを入力（例: say hello）',
  },
  msg_sending: {
    zh: () => '发送中',
    en: () => 'SENDING',
    ja: () => '送信中',
  },
  msg_sent: {
    zh: () => '已发送',
    en: () => 'SENT',
    ja: () => '送信済み',
  },
  msg_send: {
    zh: () => '发送',
    en: () => 'SEND',
    ja: () => '送信',
  },
  msg_server_stopped_you_can_prepare_a_command_and: {
    zh: () => '实例已停止，可先输入命令，启动后发送。',
    en: () => 'Server stopped. You can prepare a command and send it after starting.',
    ja: () => '停止中でもコマンドを入力できます。起動後に送信してください。',
  },
  msg_updated: {
    zh: () => '已更新 ',
    en: () => 'UPDATED ',
    ja: () => '更新済み ',
  },
  msg_disable_client_mods: {
    zh: () => '关闭客户端模组',
    en: () => 'DISABLE CLIENT MODS',
    ja: () => 'クライアント MOD を無効化',
  },
  msg_stop_the_server_before_changing_add_ons_auto: {
    zh: () => '启停需先停止实例。自动检测仅关闭元数据明确标记为客户端专用的模组，未知项目保持原样。',
    en: () =>
      'Stop the server before changing add-ons. Auto-detection only disables explicitly marked client-only mods.',
    ja: () => '変更前に停止してください。自動検出は明示的にクライアント専用とされた MOD のみ無効化します。',
  },
  msg_search_name_or_file: {
    zh: () => '搜索名称或文件',
    en: () => 'SEARCH NAME OR FILE',
    ja: () => '名前・ファイルを検索',
  },
  msg_loading_add_ons: {
    zh: () => '正在读取扩展列表…',
    en: () => 'LOADING ADD-ONS…',
    ja: () => '一覧を読み込み中…',
  },
  msg_this_core_does_not_support_plugins_or_no_plu: {
    zh: () => '该核心不支持插件或未检测到插件列表。',
    en: () => 'This core does not support plugins, or no plugins were detected.',
    ja: () => 'プラグイン非対応、または一覧が検出されませんでした。',
  },
  msg_no_files_detected: {
    zh: () => '未检测到文件',
    en: () => 'NO FILES DETECTED',
    ja: () => 'ファイルがありません',
  },
  msg_add_on_pages: {
    zh: () => '扩展分页',
    en: () => 'ADD-ON PAGES',
    ja: () => 'ページ切替',
  },
  msg_20_per_page: {
    zh: () => '每页20项',
    en: () => '20 PER PAGE',
    ja: () => '20 件/ページ',
  },
  msg_prev: {
    zh: () => '上一页',
    en: () => 'PREV',
    ja: () => '前へ',
  },
  msg_next: {
    zh: () => '下一页',
    en: () => 'NEXT',
    ja: () => '次へ',
  },
  msg_loading: {
    zh: () => '读取中',
    en: () => 'Loading',
    ja: () => '読み込み中',
  },
  msg_failed_to_delete_instance: {
    zh: () => '实例删除失败',
    en: () => 'Failed to delete instance',
    ja: () => 'インスタンスの削除に失敗しました',
  },
  msg_delete_instance: {
    zh: () => '确认删除实例',
    en: () => 'Delete instance',
    ja: () => 'インスタンスを削除',
  },
  msg_: {
    zh: () => '？',
    en: () => '?',
    ja: () => '？',
  },
  msg_this_permanently_deletes_all_server_files_an: {
    zh: () => '此操作将永久删除所有服务端文件，不可恢复！',
    en: () => 'This permanently deletes all server files and cannot be undone!',
    ja: () => 'すべてのサーバーファイルが完全に削除され、元に戻せません！',
  },
  msg_delete_2: {
    zh: () => '确认删除',
    en: () => 'DELETE',
    ja: () => '削除する',
  },
  msg_invalid_request: {
    zh: () => '请求无效',
    en: () => 'Invalid request',
    ja: () => '無効なリクエスト',
  },
  msg_the_request_is_missing_required_parameters_o: {
    zh: () => '请求缺少必要参数，或格式无法识别。请返回控制台重新操作。',
    en: () =>
      'The request is missing required parameters or has an unrecognized format. Return to the console and try again.',
    ja: () =>
      'リクエストに必要なパラメータが欠けているか、形式を認識できません。コンソールに戻ってやり直してください。',
  },
  msg_authentication_required: {
    zh: () => '需要身份验证',
    en: () => 'Authentication required',
    ja: () => '認証が必要です',
  },
  msg_your_session_has_expired_sign_in_again_to_co: {
    zh: () => '会话已失效，请重新登录后继续。',
    en: () => 'Your session has expired. Sign in again to continue.',
    ja: () => 'セッションが切れました。再度ログインして続行してください。',
  },
  msg_access_denied: {
    zh: () => '访问被拒绝',
    en: () => 'Access denied',
    ja: () => 'アクセスが拒否されました',
  },
  msg_the_current_account_does_not_have_permission: {
    zh: () => '当前账户没有访问此资源的权限。',
    en: () => 'The current account does not have permission to access this resource.',
    ja: () => '現在のアカウントにはこのリソースへのアクセス権がありません。',
  },
  msg_page_not_found: {
    zh: () => '页面不存在',
    en: () => 'Page not found',
    ja: () => 'ページが見つかりません',
  },
  msg_no_coordinates_match_this_route_return_to_th: {
    zh: () => '这条航线上没有对应的坐标。请返回控制台重新导航。',
    en: () => 'No coordinates match this route. Return to the console and navigate again.',
    ja: () => 'この航路に対応する座標はありません。コンソールに戻って再移動してください。',
  },
  msg_method_not_allowed: {
    zh: () => '请求方式不支持',
    en: () => 'Method not allowed',
    ja: () => 'メソッドが許可されていません',
  },
  msg_this_address_does_not_accept_the_current_req: {
    zh: () => '该地址不接受当前的请求方式。请从面板重新发起操作。',
    en: () => 'This address does not accept the current request method. Start the action again from the panel.',
    ja: () => 'このアドレスでは現在のリクエスト方式を受け付けません。パネルから操作をやり直してください。',
  },
  msg_request_timeout: {
    zh: () => '请求超时',
    en: () => 'Request timeout',
    ja: () => 'リクエストがタイムアウトしました',
  },
  msg_the_response_took_too_long_check_your_connec: {
    zh: () => '等待响应的时间过长，请检查网络后重试。',
    en: () => 'The response took too long. Check your connection and try again.',
    ja: () => '応答に時間がかかりすぎました。ネットワークを確認して再試行してください。',
  },
  msg_conflict: {
    zh: () => '状态冲突',
    en: () => 'Conflict',
    ja: () => '状態が競合しています',
  },
  msg_the_resource_state_has_changed_refresh_and_t: {
    zh: () => '资源状态已经变化，请刷新后再试。',
    en: () => 'The resource state has changed. Refresh and try again.',
    ja: () => 'リソースの状態が変更されました。更新してから再試行してください。',
  },
  msg_validation_failed: {
    zh: () => '数据校验失败',
    en: () => 'Validation failed',
    ja: () => 'データ検証に失敗しました',
  },
  msg_the_submitted_data_failed_validation_check_i: {
    zh: () => '提交的数据未通过校验，请检查后重试。',
    en: () => 'The submitted data failed validation. Check it and try again.',
    ja: () => '送信されたデータが検証に通りませんでした。確認して再試行してください。',
  },
  msg_too_many_requests: {
    zh: () => '请求过于频繁',
    en: () => 'Too many requests',
    ja: () => 'リクエストが多すぎます',
  },
  msg_the_request_rate_exceeded_the_limit_wait_a_m: {
    zh: () => '操作频率超出限制，请稍等片刻再试。',
    en: () => 'The request rate exceeded the limit. Wait a moment and try again.',
    ja: () => 'リクエスト頻度が制限を超えました。少し待ってから再試行してください。',
  },
  msg_internal_error: {
    zh: () => '面板内部错误',
    en: () => 'Internal error',
    ja: () => '内部エラー',
  },
  msg_the_panel_encountered_an_unexpected_error_tr: {
    zh: () => '面板运行时遇到异常，请稍后重试或查看服务日志。',
    en: () => 'The panel encountered an unexpected error. Try again later or check the service logs.',
    ja: () => 'パネルの実行中に例外が発生しました。しばらくしてから再試行するか、サービスログを確認してください。',
  },
  msg_bad_gateway: {
    zh: () => '后端连接失败',
    en: () => 'Bad gateway',
    ja: () => 'バックエンド接続エラー',
  },
  msg_the_panel_cannot_reach_the_backend_service_m: {
    zh: () => '面板无法连接到后端服务，请确认服务正在运行。',
    en: () => 'The panel cannot reach the backend service. Make sure it is running.',
    ja: () => 'パネルがバックエンドサービスに接続できません。サービスが稼働しているか確認してください。',
  },
  msg_service_unavailable: {
    zh: () => '服务暂不可用',
    en: () => 'Service unavailable',
    ja: () => 'サービスを利用できません',
  },
  msg_the_service_is_under_maintenance_or_not_read: {
    zh: () => '服务正在维护或尚未就绪，请稍后再试。',
    en: () => 'The service is under maintenance or not ready yet. Try again later.',
    ja: () => 'サービスはメンテナンス中か、まだ準備ができていません。後でもう一度お試しください。',
  },
  msg_gateway_timeout: {
    zh: () => '后端响应超时',
    en: () => 'Gateway timeout',
    ja: () => 'ゲートウェイタイムアウト',
  },
  msg_the_backend_took_too_long_to_respond_try_aga: {
    zh: () => '后端响应超时，请稍后重试。',
    en: () => 'The backend took too long to respond. Try again later.',
    ja: () => 'バックエンドの応答がタイムアウトしました。後でもう一度お試しください。',
  },
  msg_unknown_error: {
    zh: () => '未知错误',
    en: () => 'Unknown error',
    ja: () => '不明なエラー',
  },
  msg_the_request_could_not_be_completed_return_to: {
    zh: () => '请求未能完成，请返回控制台后重试。',
    en: () => 'The request could not be completed. Return to the console and try again.',
    ja: () => 'リクエストを完了できませんでした。コンソールに戻って再試行してください。',
  },
  msg_sign_in_again: {
    zh: () => '重新登录',
    en: () => 'SIGN IN AGAIN',
    ja: () => '再ログイン',
  },
  msg_reload: {
    zh: () => '重新加载',
    en: () => 'RELOAD',
    ja: () => '再読み込み',
  },
  msg_back_to_console: {
    zh: () => '返回控制台',
    en: () => 'BACK TO CONSOLE',
    ja: () => 'コンソールへ',
  },
  msg_back_to_home: {
    zh: () => '返回首页',
    en: () => 'BACK TO HOME',
    ja: () => 'ホームへ',
  },
  msg_sign_in: {
    zh: () => '返回登录',
    en: () => 'SIGN IN',
    ja: () => 'ログイン',
  },
  msg_request_failed: {
    zh: () => '请求失败',
    en: () => 'Request failed',
    ja: () => 'リクエストに失敗しました',
  },
  msg_sign_in_failed: {
    zh: () => '登录失败',
    en: () => 'Sign-in failed',
    ja: () => 'ログインに失敗しました',
  },
  msg_backend_ipv6_udp_port_is_reserved_by_another_instanc: {
    zh: () => 'IPv6 UDP 端口已被其他实例或任务预留',
    en: () => 'IPv6 UDP port is reserved by another instance or task',
    ja: () => 'IPv6 UDP ポートは他のインスタンスまたはタスクで予約されています',
  },
  msg_backend_ipv6_udp_port_is_duplicated_or_in_use: {
    zh: () => 'IPv6 UDP 端口重复或已占用',
    en: () => 'IPv6 UDP port is duplicated or in use',
    ja: () => 'IPv6 UDP ポートが重複または使用中です',
  },
  msg_backend_cannot_overwrite_a_directory: {
    zh: () => '不能覆盖目录',
    en: () => 'Cannot overwrite a directory',
    ja: () => 'ディレクトリは上書きできません',
  },
  msg_backend_you_cannot_disable_or_downgrade_your_own_adm: {
    zh: () => '不能禁用或降低自己的管理员权限',
    en: () => 'You cannot disable or downgrade your own admin rights',
    ja: () => '自分自身の管理者権限を無効化・降格できません',
  },
  msg_backend_deployment_task_not_found: {
    zh: () => '部署任务不存在',
    en: () => 'Deployment task not found',
    ja: () => 'デプロイタスクが見つかりません',
  },
  msg_backend_server_port_is_already_in_use: {
    zh: () => '服务端端口已被占用',
    en: () => 'Server port is already in use',
    ja: () => 'サーバーポートは既に使用中です',
  },
  msg_backend_invalid_server_property_key_or_value: {
    zh: () => '服务端属性键或值无效',
    en: () => 'Invalid server property key or value',
    ja: () => 'サーバープロパティのキーまたは値が無効です',
  },
  msg_backend_this_instance_or_port_is_being_deployed: {
    zh: () => '该实例或端口正在部署',
    en: () => 'This instance or port is being deployed',
    ja: () => 'このインスタンスまたはポートはデプロイ中です',
  },
  msg_backend_this_instance_is_deploying_wait_for_it_to_fi: {
    zh: () => '该实例正在部署，请等待完成',
    en: () => 'This instance is deploying; wait for it to finish',
    ja: () => 'このインスタンスはデプロイ中です。完了までお待ちください',
  },
  msg_backend_only_zip_tar_gz_or_tgz_is_supported: {
    zh: () => '仅支持 ZIP、TAR.GZ 或 TGZ',
    en: () => 'Only ZIP, TAR.GZ or TGZ is supported',
    ja: () => 'ZIP、TAR.GZ、TGZ のみ対応しています',
  },
  msg_backend_only_one_command_can_be_sent_at_a_time: {
    zh: () => '每次只能发送一条指令',
    en: () => 'Only one command can be sent at a time',
    ja: () => 'コマンドは一度に 1 つだけ送信できます',
  },
  msg_backend_password_must_be_8_72_bytes: {
    zh: () => '密码需要 8–72 字节',
    en: () => 'Password must be 8–72 bytes',
    ja: () => 'パスワードは 8–72 バイト必要です',
  },
  msg_backend_launch_target_does_not_exist_or_the_path_is_: {
    zh: () => '启动目标不存在或路径无效',
    en: () => 'Launch target does not exist or the path is invalid',
    ja: () => '起動対象が存在しないか、パスが無効です',
  },
  msg_backend_set_an_rcon_password_and_use_an_rcon_port_di: {
    zh: () => '请设置 RCON 密码，并使用不同于游戏端口的 RCON 端口',
    en: () => 'Set an RCON password and use an RCON port different from the game port',
    ja: () => 'RCON パスワードを設定し、ゲームポートと異なる RCON ポートを使用してください',
  },
  msg_backend_stop_the_instance_before_saving_to_avoid_the: {
    zh: () => '请先停止实例再保存设置，避免服务端覆盖配置文件',
    en: () => 'Stop the instance before saving to avoid the server overwriting the config',
    ja: () => 'サーバーが設定を上書きしないよう、保存前にインスタンスを停止してください',
  },
  msg_backend_select_a_game_version: {
    zh: () => '请选择游戏版本',
    en: () => 'Select a game version',
    ja: () => 'ゲームバージョンを選択してください',
  },
  msg_backend_instance_id_or_port_already_exists_or_is_bei: {
    zh: () => '实例 ID 或端口已存在或正在部署',
    en: () => 'Instance ID or port already exists or is being deployed',
    ja: () => 'インスタンス ID またはポートが既に存在するか、デプロイ中です',
  },
  msg_backend_instance_id_or_port_already_exists_manage_th: {
    zh: () => '实例 ID 或端口已存在，请管理已有实例或更换端口',
    en: () => 'Instance ID or port already exists; manage the existing instance or choose another port',
    ja: () =>
      'インスタンス ID またはポートが既に存在します。既存インスタンスを管理するか、別のポートを使用してください',
  },
  msg_backend_invalid_instance_id: {
    zh: () => '实例 ID 无效',
    en: () => 'Invalid instance ID',
    ja: () => 'インスタンス ID が無効です',
  },
  msg_backend_invalid_instance_id_port_or_runtime: {
    zh: () => '实例 ID、端口或运行环境无效',
    en: () => 'Invalid instance ID, port or runtime',
    ja: () => 'インスタンス ID、ポート、実行環境が無効です',
  },
  msg_backend_instance_not_found: {
    zh: () => '实例不存在',
    en: () => 'Instance not found',
    ja: () => 'インスタンスが見つかりません',
  },
  msg_backend_instance_process_has_exited: {
    zh: () => '实例进程已退出',
    en: () => 'Instance process has exited',
    ja: () => 'インスタンスのプロセスは終了しました',
  },
  msg_backend_instance_directory_not_found: {
    zh: () => '实例目录不存在',
    en: () => 'Instance directory not found',
    ja: () => 'インスタンスディレクトリが見つかりません',
  },
  msg_backend_instance_is_not_running_or_rcon_is_not_confi: {
    zh: () => '实例未运行或RCON未配置',
    en: () => 'Instance is not running or RCON is not configured',
    ja: () => 'インスタンスが停止中、または RCON が未設定です',
  },
  msg_backend_instance_is_not_running_or_rcon_is_not_confi_2: {
    zh: () => '实例未运行或 RCON 未配置',
    en: () => 'Instance is not running or RCON is not configured',
    ja: () => 'インスタンスが停止中、または RCON が未設定です',
  },
  msg_backend_instance_is_deploying_wait_for_it_to_finish: {
    zh: () => '实例正在部署，请等待完成',
    en: () => 'Instance is deploying; wait for it to finish',
    ja: () => 'インスタンスはデプロイ中です。完了までお待ちください',
  },
  msg_backend_world_generation_parameters_must_be_valid_js: {
    zh: () => '世界生成参数必须是有效JSON',
    en: () => 'World generation parameters must be valid JSON',
    ja: () => 'ワールド生成パラメータは有効な JSON である必要があります',
  },
  msg_backend_not_signed_in: {
    zh: () => '未登录',
    en: () => 'Not signed in',
    ja: () => 'ログインしていません',
  },
  msg_backend_file_not_found_or_larger_than_5mb: {
    zh: () => '文件不存在或超过 5MB',
    en: () => 'File not found or larger than 5MB',
    ja: () => 'ファイルが存在しないか、5MB を超えています',
  },
  msg_backend_file_exceeds_5mb: {
    zh: () => '文件超过 5MB',
    en: () => 'File exceeds 5MB',
    ja: () => 'ファイルが 5MB を超えています',
  },
  msg_backend_username_already_exists: {
    zh: () => '用户名已存在',
    en: () => 'Username already exists',
    ja: () => 'ユーザー名は既に存在します',
  },
  msg_backend_account_not_found: {
    zh: () => '账户不存在',
    en: () => 'Account not found',
    ja: () => 'アカウントが見つかりません',
  },
  msg_backend_incomplete_png: {
    zh: () => 'PNG 不完整',
    en: () => 'Incomplete PNG',
    ja: () => 'PNG が不完全です',
  },
  msg_backend_png_validation_failed: {
    zh: () => 'PNG 校验失败',
    en: () => 'PNG validation failed',
    ja: () => 'PNG の検証に失敗しました',
  },
  msg_backend_you_can_t_delete_others_tasks: {
    zh: () => '不可删除他人的任务',
    en: () => "You can't delete others' tasks",
    ja: () => '他のユーザーのタスクは削除できません',
  },
  msg_backend_you_can_t_modify_others_tasks: {
    zh: () => '不可修改他人的任务',
    en: () => "You can't modify others' tasks",
    ja: () => '他のユーザーのタスクは変更できません',
  },
  msg_backend_you_can_t_run_others_tasks: {
    zh: () => '不可运行他人的任务',
    en: () => "You can't run others' tasks",
    ja: () => '他のユーザーのタスクは実行できません',
  },
  msg_backend_you_can_t_delete_the_current_account: {
    zh: () => '不能删除当前账户',
    en: () => "You can't delete the current account",
    ja: () => '現在のアカウントは削除できません',
  },
  msg_backend_current_password_is_incorrect: {
    zh: () => '当前密码不正确',
    en: () => 'Current password is incorrect',
    ja: () => '現在のパスワードが正しくありません',
  },
  msg_backend_export_failed: {
    zh: () => '导出失败',
    en: () => 'Export failed',
    ja: () => 'エクスポートに失敗しました',
  },
  msg_backend_too_many_login_attempts: {
    zh: () => '登录尝试过多',
    en: () => 'Too many login attempts',
    ja: () => 'ログイン試行回数が多すぎます',
  },
  msg_backend_two_factor_authentication_is_already_enabled: {
    zh: () => '二步验证已启用',
    en: () => 'Two-factor authentication is already enabled',
    ja: () => '二段階認証は既に有効です',
  },
  msg_backend_no_accessible_stable_release_yet: {
    zh: () => '发布源尚无可访问的正式版本',
    en: () => 'No accessible stable release yet',
    ja: () => 'アクセス可能な正式版がまだありません',
  },
  msg_backend_update_package_not_found: {
    zh: () => '更新包不存在',
    en: () => 'Update package not found',
    ja: () => '更新パッケージが見つかりません',
  },
  msg_backend_official_bds_is_only_available_for_windows_u: {
    zh: () => '官方 BDS 仅提供 Windows / Ubuntu x86_64 版本',
    en: () => 'Official BDS is only available for Windows / Ubuntu x86_64',
    ja: () => '公式 BDS は Windows / Ubuntu x86_64 のみ提供されています',
  },
  msg_backend_failed_to_fetch_official_bedrock_versions: {
    zh: () => '获取官方基岩版版本失败',
    en: () => 'Failed to fetch official Bedrock versions',
    ja: () => '公式 Bedrock バージョンの取得に失敗しました',
  },
  msg_backend_failed_to_check_for_updates: {
    zh: () => '检查更新失败',
    en: () => 'Failed to check for updates',
    ja: () => '更新の確認に失敗しました',
  },
  msg_backend_no_permission_for_task_operations: {
    zh: () => '没有任务操作权限',
    en: () => 'No permission for task operations',
    ja: () => 'タスク操作の権限がありません',
  },
  msg_backend_no_permission_for_the_selected_instances: {
    zh: () => '没有所选实例的操作权限',
    en: () => 'No permission for the selected instances',
    ja: () => '選択したインスタンスの操作権限がありません',
  },
  msg_backend_incorrect_password: {
    zh: () => '密码错误',
    en: () => 'Incorrect password',
    ja: () => 'パスワードが正しくありません',
  },
  msg_backend_target_file_already_exists: {
    zh: () => '目标文件已存在',
    en: () => 'Target file already exists',
    ja: () => '対象ファイルは既に存在します',
  },
  msg_backend_use_the_new_wizard_to_pick_a_bedrock_version: {
    zh: () => '请使用新版向导选择基岩版版本并确认EULA',
    en: () => 'Use the new wizard to pick a Bedrock version and accept the EULA',
    ja: () => '新しいウィザードで Bedrock バージョンを選択し、EULA に同意してください',
  },
  msg_backend_enter_a_single_line_command: {
    zh: () => '请输入单行命令',
    en: () => 'Enter a single-line command',
    ja: () => '1 行のコマンドを入力してください',
  },
  msg_backend_enter_the_six_digit_code_from_your_authentic: {
    zh: () => '请输入验证器中的六位验证码',
    en: () => 'Enter the six-digit code from your authenticator',
    ja: () => '認証アプリの 6 桁コードを入力してください',
  },
  msg_backend_accept_the_minecraft_eula_and_set_different_: {
    zh: () => '请同意 Minecraft EULA，并设置不同的 IPv4 / IPv6 UDP 端口',
    en: () => 'Accept the Minecraft EULA and set different IPv4 / IPv6 UDP ports',
    ja: () => 'Minecraft EULA に同意し、IPv4 / IPv6 UDP ポートを別々に設定してください',
  },
  msg_backend_disable_https_before_replacing_the_certifica: {
    zh: () => '请先关闭HTTPS再替换证书',
    en: () => 'Disable HTTPS before replacing the certificate',
    ja: () => '証明書を差し替える前に HTTPS を無効化してください',
  },
  msg_backend_stop_the_instance_first: {
    zh: () => '请先停止实例',
    en: () => 'Stop the instance first',
    ja: () => '先にインスタンスを停止してください',
  },
  msg_backend_stop_the_instance_first_to_keep_the_world_sa: {
    zh: () => '请先停止实例，确保世界存档一致',
    en: () => 'Stop the instance first to keep the world save consistent',
    ja: () => 'ワールドの整合性のため、先にインスタンスを停止してください',
  },
  msg_backend_task_not_found: {
    zh: () => '任务不存在',
    en: () => 'Task not found',
    ja: () => 'タスクが見つかりません',
  },
  msg_backend_no_icon_set_yet: {
    zh: () => '尚未设置图标',
    en: () => 'No icon set yet',
    ja: () => 'アイコンが未設定です',
  },
}
export const commonMessages: Record<string, Record<Locale, () => string>> = text
