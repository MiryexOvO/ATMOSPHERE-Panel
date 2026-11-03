type Locale = 'zh' | 'en' | 'ja'
const text: Record<string, Record<Locale, () => string>> = {
  accountSecurity: {
    zh: () => '账户安全',
    en: () => 'ACCOUNT SECURITY',
    ja: () => 'アカウント保護',
  },
  passwordCurrent: {
    zh: () => '当前密码',
    en: () => 'CURRENT PASSWORD',
    ja: () => '現在のパスワード',
  },
  passwordNew: {
    zh: () => '新密码',
    en: () => 'NEW PASSWORD',
    ja: () => '新しいパスワード',
  },
  passwordConfirm: {
    zh: () => '确认新密码',
    en: () => 'CONFIRM NEW PASSWORD',
    ja: () => '新しいパスワードを確認',
  },
  passwordMismatch: {
    zh: () => '两次输入的新密码不同',
    en: () => 'The new passwords do not match',
    ja: () => '新しいパスワードが一致しません',
  },
  tabConsole: {
    zh: () => '控制台',
    en: () => 'CONSOLE',
    ja: () => 'コンソール',
  },
  tabMonitor: {
    zh: () => '性能监测',
    en: () => 'MONITOR',
    ja: () => 'モニター',
  },
  tabFiles: {
    zh: () => '文件管理',
    en: () => 'FILES',
    ja: () => 'ファイル',
  },
  tabBackups: {
    zh: () => '备份',
    en: () => 'BACKUPS',
    ja: () => 'バックアップ',
  },
  tabInstanceSettings: {
    zh: () => '设置',
    en: () => 'SETTINGS',
    ja: () => '設定',
  },
  fileRefresh: {
    zh: () => '刷新',
    en: () => 'REFRESH',
    ja: () => '更新',
  },
  fileUpload: {
    zh: () => '上传文件',
    en: () => 'UPLOAD',
    ja: () => 'アップロード',
  },
  fileNew: {
    zh: () => '新建文件',
    en: () => 'NEW FILE',
    ja: () => '新規ファイル',
  },
  fileFolder: {
    zh: () => '新建目录',
    en: () => 'NEW FOLDER',
    ja: () => '新規フォルダー',
  },
  fileRename: {
    zh: () => '重命名 / 移动',
    en: () => 'RENAME / MOVE',
    ja: () => '名前変更・移動',
  },
  fileCopy: {
    zh: () => '复制',
    en: () => 'COPY',
    ja: () => 'コピー',
  },
  fileDelete: {
    zh: () => '删除',
    en: () => 'DELETE',
    ja: () => '削除',
  },
  fileExtract: {
    zh: () => '解压',
    en: () => 'EXTRACT',
    ja: () => '展開',
  },
  fileCompress: {
    zh: () => '压缩',
    en: () => 'COMPRESS',
    ja: () => '圧縮',
  },
  fileDownload: {
    zh: () => '下载',
    en: () => 'DOWNLOAD',
    ja: () => 'ダウンロード',
  },
  fileSave: {
    zh: () => '保存',
    en: () => 'SAVE',
    ja: () => '保存',
  },
  fileCancel: {
    zh: () => '取消',
    en: () => 'CANCEL',
    ja: () => 'キャンセル',
  },
  fileConfirm: {
    zh: () => '确认操作',
    en: () => 'CONFIRM',
    ja: () => '実行',
  },
  fileTarget: {
    zh: () => '文件路径 / 目标路径',
    en: () => 'FILE / DESTINATION PATH',
    ja: () => 'ファイル・保存先パス',
  },
  fileDeleteHint: {
    zh: () => '将永久删除此路径及其内容，请确认：',
    en: () => 'Permanently delete this path and its contents:',
    ja: () => '次のパスと内容を完全に削除します：',
  },
  fileDone: {
    zh: () => '操作完成',
    en: () => 'Operation completed',
    ja: () => '完了しました',
  },
  fileSelect: {
    zh: () => '选择文本文件开始编辑，或拖入文件上传',
    en: () => 'Select a text file to edit, or drop files to upload',
    ja: () => 'テキストファイルを選択、またはファイルをドロップ',
  },
  fileUnsaved: {
    zh: () => '当前文件未保存，是否放弃修改？',
    en: () => 'Discard unsaved changes?',
    ja: () => '未保存の変更を破棄しますか？',
  },
  fileEmpty: {
    zh: () => '此目录为空',
    en: () => 'This directory is empty',
    ja: () => '空のディレクトリです',
  },
  monitorTitle: {
    zh: () => '实例资源遥测',
    en: () => 'INSTANCE TELEMETRY',
    ja: () => 'インスタンス計測',
  },
  monitorHint: {
    zh: () => '仅统计此实例的 Java 进程树。CPU 100% 代表占满一个逻辑核心。',
    en: () => 'Only this instance’s Java process tree. CPU 100% equals one logical core.',
    ja: () => 'このインスタンスの Java プロセス群のみ計測。CPU 100% は論理コア1個分です。',
  },
  monitorCpu: {
    zh: () => 'CPU 占用',
    en: () => 'CPU USAGE',
    ja: () => 'CPU 使用率',
  },
  monitorMemory: {
    zh: () => '物理内存占用',
    en: () => 'RESIDENT MEMORY',
    ja: () => '物理メモリ使用量',
  },
  monitorThreads: {
    zh: () => '线程数',
    en: () => 'THREADS',
    ja: () => 'スレッド数',
  },
  monitorUptime: {
    zh: () => '运行时长',
    en: () => 'UPTIME',
    ja: () => '稼働時間',
  },
  monitorRead: {
    zh: () => '磁盘读取',
    en: () => 'DISK READ',
    ja: () => 'ディスク読み取り',
  },
  monitorWrite: {
    zh: () => '磁盘写入',
    en: () => 'DISK WRITE',
    ja: () => 'ディスク書き込み',
  },
  monitorOffline: {
    zh: () => '实例未运行',
    en: () => 'INSTANCE OFFLINE',
    ja: () => 'インスタンスは停止中',
  },
  monitorSample: {
    zh: () => '最近采样',
    en: () => 'RECENT SAMPLES',
    ja: () => '直近のサンプル',
  },
  monitorHostShare: {
    zh: () => '占主机 CPU',
    en: () => 'HOST CPU SHARE',
    ja: () => 'ホスト CPU 比率',
  },
  panelSettingsTitle: {
    zh: () => '面板基础设置',
    en: () => 'PANEL PREFERENCES',
    ja: () => 'パネル基本設定',
  },
  panelName: {
    zh: () => '面板名称',
    en: () => 'PANEL NAME',
    ja: () => 'パネル名',
  },
  panelSession: {
    zh: () => '登录有效期（小时）',
    en: () => 'SESSION HOURS',
    ja: () => 'セッション有効期間（時間）',
  },
  panelMemory: {
    zh: () => '默认内存（MB）',
    en: () => 'DEFAULT MEMORY (MB)',
    ja: () => '既定メモリ（MB）',
  },
  panelJava: {
    zh: () => '默认 Java',
    en: () => 'DEFAULT JAVA',
    ja: () => '既定 Java',
  },
  panelPort: {
    zh: () => '默认游戏端口',
    en: () => 'DEFAULT GAME PORT',
    ja: () => '既定ゲームポート',
  },
  panelInterval: {
    zh: () => '资源采样间隔（秒）',
    en: () => 'SAMPLE INTERVAL (SECONDS)',
    ja: () => '計測間隔（秒）',
  },
  panelLanguage: {
    zh: () => '默认语言',
    en: () => 'DEFAULT LANGUAGE',
    ja: () => '既定の言語',
  },
  panelUpload: {
    zh: () => '单文件上传上限（MB）',
    en: () => 'UPLOAD LIMIT (MB)',
    ja: () => 'アップロード上限（MB）',
  },
  panelSaved: {
    zh: () => '设置已保存',
    en: () => 'Settings saved',
    ja: () => '設定を保存しました',
  },
  panelSourceHint: {
    zh: () => '默认模式对同版本、同构建的可用源并行测速；手动选择时只使用指定源。来源没有该构建时会明确报错。',
    en: () =>
      'Automatic mode probes matching version/build sources in parallel. Manual mode uses only the selected source and reports unavailable builds.',
    ja: () =>
      '自動では同一バージョン・ビルドの提供元を並列計測。手動では指定した提供元のみを使用し、未提供の場合はエラーを表示します。',
  },
  usersTitle: {
    zh: () => '用户与访问权限',
    en: () => 'USERS & ACCESS',
    ja: () => 'ユーザーとアクセス権',
  },
  usersNew: {
    zh: () => '创建用户',
    en: () => 'CREATE USER',
    ja: () => 'ユーザー作成',
  },
  usersName: {
    zh: () => '用户名',
    en: () => 'USERNAME',
    ja: () => 'ユーザー名',
  },
  usersPassword: {
    zh: () => '密码（编辑时留空表示不修改）',
    en: () => 'PASSWORD (BLANK TO KEEP)',
    ja: () => 'パスワード（空欄で維持）',
  },
  usersRole: {
    zh: () => '权限角色',
    en: () => 'ROLE',
    ja: () => '権限',
  },
  usersEnabled: {
    zh: () => '允许登录',
    en: () => 'LOGIN ENABLED',
    ja: () => 'ログイン許可',
  },
  usersEdit: {
    zh: () => '编辑',
    en: () => 'EDIT',
    ja: () => '編集',
  },
  usersRevoke: {
    zh: () => '注销会话',
    en: () => 'REVOKE SESSIONS',
    ja: () => 'セッション失効',
  },
  usersAdmin: {
    zh: () => '管理员',
    en: () => 'ADMINISTRATOR',
    ja: () => '管理者',
  },
  usersOperator: {
    zh: () => '实例操作员',
    en: () => 'OPERATOR',
    ja: () => 'オペレーター',
  },
  usersViewer: {
    zh: () => '只读用户',
    en: () => 'READ ONLY',
    ja: () => '閲覧のみ',
  },
  usersRoleHint: {
    zh: () => '管理员管理面板与账户；操作员管理实例；只读用户仅查看状态、监测和日志。',
    en: () =>
      'Administrators manage the panel and accounts. Operators manage instances. Viewers can read status, metrics and logs.',
    ja: () =>
      '管理者はパネルとアカウント、オペレーターはインスタンスを管理。閲覧者は状態・計測値・ログのみ閲覧可能です。',
  },
  usersAudit: {
    zh: () => '最近管理活动',
    en: () => 'RECENT ADMIN ACTIVITY',
    ja: () => '最近の管理操作',
  },
  usersDelete: {
    zh: () => '确认删除此账户？',
    en: () => 'Delete this account?',
    ja: () => 'このアカウントを削除しますか？',
  },
}
export const panelMessages: Record<string, Record<Locale, () => string>> = text
