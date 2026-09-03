"""Content formatters that render extracted values for preview."""

import json
import re
from io import StringIO
from typing import Any, assert_never

import tomli_w
from ruamel.yaml import YAML

from vcr_tui.config.models import FormatterType

_yaml = YAML()
_yaml.default_flow_style = False


def format_content(content: Any, formatter: FormatterType) -> str:
    """Render a value as a preview string using the named formatter."""
    match formatter:
        case 'json':
            return _format_json(content)
        case 'yaml':
            return _format_yaml(content)
        case 'text':
            return _format_text(content)
        case 'html':
            return _format_html(content)
        case 'toml':
            return _format_toml(content)
        case _:
            assert_never(formatter)


def _format_json(content: Any) -> str:
    if isinstance(content, str):
        try:
            parsed = json.loads(content)
            return json.dumps(parsed, indent=2)
        except json.JSONDecodeError:
            return content
    return json.dumps(content, indent=2)


def _format_yaml(content: Any) -> str:
    stream = StringIO()
    _yaml.dump(_expand_json_strings(content), stream)
    text = stream.getvalue().rstrip()
    # A bare scalar (str/int/...) is emitted with a trailing "..." document-end
    # marker on its own line, which is noise in a preview; drop it.
    return text.removesuffix('\n...')


def _format_text(content: Any) -> str:
    if not isinstance(content, str):
        return str(content)
    return content.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '')


_TAG_RE = re.compile(r'<[^>]*>')


def _format_html(content: Any) -> str:
    """Pretty-print well-formed markup, falling back to the verbatim string."""
    if not isinstance(content, str):
        return str(content)
    try:
        return _indent_markup(content)
    except _MalformedMarkupError:
        return content


class _MalformedMarkupError(Exception):
    """Raised internally when markup does not look well-formed."""


def _normalize_html_to_xml(content: str) -> str:
    """Rewrite HTML void tags as self-closing so they balance like XML."""
    void_tags = (
        'area',
        'base',
        'br',
        'col',
        'embed',
        'hr',
        'img',
        'input',
        'link',
        'meta',
        'param',
        'source',
        'track',
        'wbr',
    )
    pattern = re.compile(
        r'<(' + '|'.join(void_tags) + r')((?:[^>"]|"[^"]*")*?)\s*/?>',
        flags=re.IGNORECASE,
    )
    return pattern.sub(r'<\1\2 />', content)


def _indent_markup(content: str) -> str:
    """Re-emit tag soup one element per line with two-space nesting.

    Tags are only tokenized and stacked, never parsed as XML, so no entity
    or DTD processing ever runs on the previewed content.
    """
    normalized = _normalize_html_to_xml(content)
    lines: list[str] = []
    stack: list[str] = []
    pos = 0
    for match in _TAG_RE.finditer(normalized):
        text = normalized[pos : match.start()]
        if text.strip():
            lines.append('  ' * len(stack) + text.strip())
        pos = match.end()
        tag = match.group(0)
        name = tag[1:].lstrip('/').split()[0].rstrip('/')
        if tag.startswith(('<?', '<!')):
            lines.append('  ' * len(stack) + tag)
        elif tag.startswith('</'):
            if not stack or stack[-1] != name:
                raise _MalformedMarkupError from None
            stack.pop()
            lines.append('  ' * len(stack) + tag)
        elif tag.endswith('/>'):
            lines.append('  ' * len(stack) + tag)
        else:
            lines.append('  ' * len(stack) + tag)
            stack.append(name)
    trailing = normalized[pos:]
    if trailing.strip():
        lines.append('  ' * len(stack) + trailing.strip())
    if stack:
        raise _MalformedMarkupError from None
    return '\n'.join(lines)


def _format_toml(content: Any) -> str:
    if isinstance(content, str):
        return content
    try:
        return tomli_w.dumps(content)
    except Exception:
        # tomli_w only writes tables; fall back to a plain representation for
        # anything else (scalars, lists of scalars, mixed data).
        return str(content)


def _expand_json_strings(data: Any) -> Any:
    """Copy ``data`` with every JSON-object/array string parsed into structure.

    Strings that are not JSON, are invalid JSON, or parse to a bare scalar
    (number, boolean, null) are kept exactly as they are.
    """
    if isinstance(data, dict):
        return {key: _expand_json_strings(value) for key, value in data.items()}
    if isinstance(data, list):
        return [_expand_json_strings(item) for item in data]
    if isinstance(data, str):
        try:
            parsed = json.loads(data)
        except json.JSONDecodeError:
            return data
        if isinstance(parsed, (dict, list)):
            return _expand_json_strings(parsed)
        return data
    return data
