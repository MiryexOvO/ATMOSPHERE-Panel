// 路径
export function instancePath(instanceId: string, suffix = ''): string {
  const base = `/api/instances/${encodeURIComponent(instanceId)}`
  if (!suffix) return base
  return base + (suffix.startsWith('/') ? suffix : `/${suffix}`)
}
