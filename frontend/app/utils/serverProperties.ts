// 兼容旧接口的 Java 属性文本，不暴露文本编辑器。
export function parseServerProperties(text: string): Record<string, string> {
  const values: Record<string, string> = {}
  let pending = ''
  const decode = (value: string) =>
    value.replace(/\\(u[0-9a-fA-F]{4}|.)/g, (_, token: string) =>
      token.startsWith('u') && token.length === 5
        ? String.fromCharCode(parseInt(token.slice(1), 16))
        : (({ n: '\n', r: '\r', t: '\t', f: '\f' } as Record<string, string>)[token] ?? token),
    )
  for (const raw of text.split(/\r?\n/)) {
    if (!pending && /^\s*(?:[#!]|$)/.test(raw)) continue
    const line = pending + (pending ? raw.trimStart() : raw)
    if ((line.match(/\\+$/)?.[0].length || 0) % 2) {
      pending = line.slice(0, -1)
      continue
    }
    pending = ''
    const entry = line.trimStart().match(/^((?:\\.|[^=:\s])+)(?:\s*[=:]\s*|\s+)?(.*)$/)
    if (entry) values[decode(entry[1]!)] = decode(entry[2]!)
  }
  return values
}

// 连接参数只在实例设置展示，属性页不重复。
export const instancePropertyKeys = new Set([
  'server-port',
  'server-portv6',
  'server-ip',
  'enable-rcon',
  'rcon.port',
  'rcon.password',
  'enable-query',
  'query.port',
])
