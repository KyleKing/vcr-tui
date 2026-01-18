import json
from io import StringIO
from typing import Any, Literal

from ruamel.yaml import YAML

FormatterType = Literal["html", "json", "text", "toml", "yaml"]

_yaml = YAML()
_yaml.default_flow_style = False


def format_content(content: Any, formatter: FormatterType) -> str:
    match formatter:
        case "json":
            return _format_json(content)
        case "yaml":
            return _format_yaml(content)
        case "text":
            return _format_text(content)
        case "html":
            return _format_html(content)
        case "toml":
            return _format_toml(content)
        case _:
            return str(content)


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
    _yaml.dump(content, stream)
    return stream.getvalue().rstrip()


def _format_text(content: Any) -> str:
    if not isinstance(content, str):
        return str(content)
    return content.replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "")


def _format_html(content: Any) -> str:
    if not isinstance(content, str):
        return str(content)
    try:
        from xml.dom.minidom import parseString
        dom = parseString(content)
        return dom.toprettyxml(indent="  ")
    except Exception:
        return content


def _format_toml(content: Any) -> str:
    if isinstance(content, str):
        return content
    try:
        import tomli_w
        return tomli_w.dumps(content)
    except ImportError:
        return str(content)
