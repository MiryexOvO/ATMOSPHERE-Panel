type Locale = 'zh' | 'en' | 'ja'

// 每个文案键都必须同时提供 zh / en / ja
type I18nMessagesSatisfiesType = Record<string, Record<Locale, () => string>>

export const i18nMessages = {
  authRequired: {
    zh: () => '/ 需要身份验证',
    en: () => '/ AUTHENTICATION REQUIRED',
    ja: () => '/ 認証が必要です',
  },
  titleEnter: {
    zh: () => 'ENTER',
    en: () => 'ENTER',
    ja: () => 'ENTER',
  },
  titleAtmosphere: {
    zh: () => 'THE ATMOSPHERE.',
    en: () => 'THE ATMOSPHERE.',
    ja: () => 'THE ATMOSPHERE.',
  },
  desc1: {
    zh: () => '一个克制、可靠的 Minecraft 服务端控制台。',
    en: () => 'A restrained, reliable Minecraft server console.',
    ja: () => '抑制された、信頼性の高いMinecraftサーバーコンソール。',
  },
  desc2: {
    zh: () => '请使用管理员凭据继续。',
    en: () => 'Please proceed with administrator credentials.',
    ja: () => '管理者の資格情報で続行してください。',
  },
  labelUsername: {
    zh: () => '管理员账号',
    en: () => 'Admin Account',
    ja: () => '管理者アカウント',
  },
  labelPassword: {
    zh: () => '访问密码',
    en: () => 'Password',
    ja: () => 'アクセスパスワード',
  },
  placeholderCredentials: {
    zh: () => '请输入凭据',
    en: () => 'Enter credentials',
    ja: () => '認証情報を入力',
  },
  btnLogin: {
    zh: () => '进入控制台',
    en: () => 'Enter Console',
    ja: () => 'コンソールへ',
  },
  btnLoading: {
    zh: () => '验证中...',
    en: () => 'Verifying...',
    ja: () => '検証中...',
  },
  apiConnected: {
    zh: () => '已连接',
    en: () => 'CONNECTED',
    ja: () => '接続済み',
  },
  apiOffline: {
    zh: () => '离线',
    en: () => 'OFFLINE',
    ja: () => 'オフライン',
  },
  sessionInfo: {
    zh: () => 'SESSION / HTTPONLY · SAME-SITE LAX',
    en: () => 'SESSION / HTTPONLY · SAME-SITE LAX',
    ja: () => 'SESSION / HTTPONLY · SAME-SITE LAX',
  },
  sessionDesc: {
    zh: () => '默认会话有效期 24 小时',
    en: () => 'Default session validity: 24 hours',
    ja: () => 'セッション有効期間：24時間',
  },
  backToControlRoom: {
    zh: () => '返回控制台',
    en: () => 'BACK TO CONTROL ROOM',
    ja: () => 'コントロールルームに戻る',
  },
  language: {
    zh: () => '语言',
    en: () => 'Language',
    ja: () => '言語',
  },
} as const satisfies I18nMessagesSatisfiesType

const locales: Locale[] = ['zh', 'en', 'ja']

// 把上面的按键字典展开成运行时格式
function toLocaleMessages(messages: typeof i18nMessages) {
  const result = { zh: {}, en: {}, ja: {} } as Record<Locale, Record<string, string>>
  for (const [key, entry] of Object.entries(messages)) {
    for (const locale of locales) result[locale][key] = entry[locale]()
  }
  return result
}

export const messages = toLocaleMessages(i18nMessages)

export type MessageKey = keyof typeof i18nMessages
export type MessageSchema = Record<MessageKey, string>

export default {
  legacy: false,
  messages,
}
