"""Read and patch Java properties while preserving comments and unknown keys."""
import re
from pathlib import Path


def _unescape(value: str) -> str:
    def decode(match):
        token = match.group(1)
        if token.startswith('u') and len(token) == 5:
            return chr(int(token[1:], 16))
        return {'n': '\n', 'r': '\r', 't': '\t', 'f': '\f'}.get(token, token)
    decoded = re.sub(r'\\(u[0-9a-fA-F]{4}|.)', decode, value)
    # Java Unicode 转义可能使用 UTF-16 代理对。
    if any(0xD800 <= ord(char) <= 0xDFFF for char in decoded):
        decoded = decoded.encode('utf-16', errors='surrogatepass').decode('utf-16', errors='replace')
    return decoded


def _entries(text: str):
    # 合并 Java 续行，保留注释原文。
    pending = []
    for line in text.splitlines():
        if not pending and (not line.strip() or line.lstrip().startswith(('#', '!'))):
            yield None, None, line
            continue
        pending.append(line)
        if (len(line) - len(line.rstrip('\\'))) % 2:
            continue
        raw = '\n'.join(pending)
        logical = ''.join(part[:-1] if i < len(pending) - 1 else part
                          for i, part in enumerate([pending[0], *[p.lstrip() for p in pending[1:]]]))
        pending = []
        stripped = logical.lstrip()
        if not stripped or stripped.startswith(('#', '!')):
            yield None, None, raw
            continue
        match = re.match(r'((?:\\.|[^=:\s])+)(?:\s*[=:]\s*|\s+)?(.*)', stripped)
        if match:
            yield _unescape(match[1]), _unescape(match[2]), raw
        else:
            yield None, None, raw
    if pending:
        yield None, None, '\n'.join(pending)


def parse_properties(text: str) -> dict[str, str]:
    return {key: value for key, value, _ in _entries(text) if key is not None}


def patch_properties(text: str, values: dict[str, str]) -> str:
    # 只修改提交的键，其余内容原样保留。
    def escape(value):
        value = str(value).replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        return ('\\' + value) if value.startswith(' ') else value
    output, seen = [], set()
    for key, _, raw in _entries(text):
        if key in values:
            if key not in seen:
                output.append(f'{key}={escape(values[key])}')
                seen.add(key)
        else:
            output.append(raw)
    output.extend(f'{key}={escape(value)}' for key, value in values.items() if key not in seen)
    return '\n'.join(output) + '\n'


def write_properties(path: Path, values: dict[str, str]):
    text = path.read_text(encoding='utf-8') if path.exists() else ''
    updated = patch_properties(text, values)
    temp = path.with_suffix('.properties.tmp')
    temp.write_text(updated, encoding='utf-8')
    temp.replace(path)
