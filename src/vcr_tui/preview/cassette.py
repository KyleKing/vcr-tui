# Copyright (c) 2026 Kyle King
# SPDX-License-Identifier: MIT
"""Parse recorded HTTP interactions out of loaded cassette data.

Works on data already loaded from YAML, so it needs nothing beyond the standard
library. Two layouts are recognised:

- vcrpy / pytest-recording: a top-level ``interactions`` list, where a request
  body is stored inline and a response body under ``body.string``.
- Ruby VCR: a top-level ``http_interactions`` list, where both bodies are
  mappings carrying ``string`` or ``base64_string``.
"""

from __future__ import annotations

import base64
import binascii
import gzip
import json
import zlib
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal
from urllib.parse import parse_qsl, urlsplit

BodyKind = Literal['empty', 'json', 'form', 'html', 'xml', 'text', 'binary']

_GZIP_MAGIC = b'\x1f\x8b'
_KIB = 1024
_MIB = _KIB * _KIB
_INTERACTION_LISTS = ('interactions', 'http_interactions')


@dataclass(frozen=True)
class Body:
    """A decoded HTTP body ready to display."""

    text: str
    kind: BodyKind
    size: int
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class HttpMessage:
    """Headers plus decoded body of one side of an interaction."""

    headers: dict[str, list[str]]
    body: Body

    def header(self, name: str) -> str:
        """Return the first value of a header, matched case-insensitively, or ''."""
        return _header(self.headers, name)


@dataclass(frozen=True)
class Interaction:
    """One recorded request/response pair."""

    index: int
    method: str
    uri: str
    status_code: int | None
    status_message: str
    request: HttpMessage
    response: HttpMessage
    recorded_at: str | None = None
    query: tuple[tuple[str, str], ...] = ()

    @property
    def host(self) -> str:
        """The URI's host, or '' when the URI has none."""
        return urlsplit(self.uri).netloc

    @property
    def path(self) -> str:
        """The URI's path plus query string."""
        parts = urlsplit(self.uri)
        path = parts.path or '/'
        return f'{path}?{parts.query}' if parts.query else path

    @property
    def status(self) -> str:
        """The status code and message, e.g. '201 Created', or '-' when absent."""
        if self.status_code is None:
            return '-'
        return f'{self.status_code} {self.status_message}'.strip()


def is_cassette(data: object) -> bool:
    """Report whether loaded data looks like a VCR cassette."""
    return isinstance(data, Mapping) and any(
        isinstance(data.get(key), list) for key in _INTERACTION_LISTS
    )


def parse_cassette(data: object) -> list[Interaction]:
    """Turn loaded cassette data into interactions, skipping malformed entries.

    Returns:
        The interactions in recorded order, or empty when the data is no cassette.
    """
    if not isinstance(data, Mapping):
        return []
    entries: object = next(
        (data[key] for key in _INTERACTION_LISTS if isinstance(data.get(key), list)),
        [],
    )
    if not isinstance(entries, list):
        return []
    interactions: list[Interaction] = []
    for index, entry in enumerate(entries):
        if isinstance(entry, Mapping):
            interactions.append(_parse_interaction(index, entry))
    return interactions


def format_row(interaction: Interaction) -> str:
    """Render an interaction as one aligned summary line."""
    code = str(interaction.status_code) if interaction.status_code is not None else '-'
    size = human_size(interaction.response.body.size)
    return (
        f'{interaction.index:>3}  {interaction.method:<7} {code:>3}  '
        f'{size:>7}  {interaction.host}{interaction.path}'
    )


def human_size(size: int) -> str:
    """Format a byte count compactly, e.g. 512 B or 1.5 KB."""
    if size < _KIB:
        return f'{size} B'
    if size < _MIB:
        return f'{size / _KIB:.1f} KB'
    return f'{size / _MIB:.1f} MB'


def decode_body(raw: object, headers: Mapping[str, object] | None = None) -> Body:
    """Decode a stored body into display text, guided by the message headers.

    Handles str and bytes (``!!binary``) bodies, gzip or deflate compression,
    JSON (pretty-printed), form-encoded data (one pair per line), and falls
    back to a size placeholder for bytes that are not UTF-8.

    Returns:
        The decoded body.
    """
    headers = headers or {}
    if raw is None or (isinstance(raw, (str, bytes, bytearray)) and not raw):
        return Body(text='', kind='empty', size=0)

    notes: list[str] = []
    if isinstance(raw, (bytes, bytearray)):
        data = _decompress(bytes(raw), _header(headers, 'content-encoding').lower(), notes)
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError:
            return Body(
                text=f'<{len(data)} bytes of binary data>',
                kind='binary',
                size=len(data),
                notes=tuple(notes),
            )
    else:
        text = str(raw)

    size = len(text.encode('utf-8'))
    kind, pretty = _classify(text, _header(headers, 'content-type').lower())
    return Body(text=pretty, kind=kind, size=size, notes=tuple(notes))


def _decompress(data: bytes, encoding: str, notes: list[str]) -> bytes:
    if data.startswith(_GZIP_MAGIC):
        try:
            result = gzip.decompress(data)
        except (OSError, EOFError, zlib.error):
            return data
        notes.append('gzip-decoded')
        return result
    if 'deflate' in encoding:
        for wbits in (zlib.MAX_WBITS, -zlib.MAX_WBITS):
            try:
                result = zlib.decompress(data, wbits)
            except zlib.error:
                continue
            notes.append('deflate-decoded')
            return result
    return data


def _classify(text: str, content_type: str) -> tuple[BodyKind, str]:
    stripped = text.lstrip()
    if 'json' in content_type or stripped[:1] in {'{', '['}:
        try:
            parsed = json.loads(text)
        except ValueError:
            pass
        else:
            return 'json', json.dumps(parsed, indent=2, ensure_ascii=False)
    if 'x-www-form-urlencoded' in content_type:
        pairs = parse_qsl(text, keep_blank_values=True)
        if pairs:
            return 'form', '\n'.join(f'{key} = {value}' for key, value in pairs)
    if 'html' in content_type or stripped[:5].lower() in {'<!doc', '<html'}:
        return 'html', text
    if 'xml' in content_type or stripped.startswith('<?xml'):
        return 'xml', text
    return 'text', text


def _header(headers: Mapping[str, object], name: str) -> str:
    wanted = name.casefold()
    for key, value in headers.items():
        if str(key).casefold() == wanted:
            if isinstance(value, list):
                return str(value[0]) if value else ''
            return str(value)
    return ''


def _normalize_headers(raw: object) -> dict[str, list[str]]:
    if not isinstance(raw, Mapping):
        return {}
    headers: dict[str, list[str]] = {}
    for key, value in raw.items():
        values = value if isinstance(value, list) else [value]
        headers[str(key)] = [str(v) for v in values]
    return headers


def _raw_body(body: object) -> object:
    """Unwrap a body to its stored str/bytes, whichever layout stored it."""
    if not isinstance(body, Mapping):
        return body
    if body.get('base64_string') is not None:
        try:
            return base64.b64decode(str(body['base64_string']))
        except (binascii.Error, ValueError):
            return str(body['base64_string'])
    return body.get('string')


def _parse_message(raw: object) -> HttpMessage:
    message = raw if isinstance(raw, Mapping) else {}
    headers = _normalize_headers(message.get('headers'))
    return HttpMessage(headers=headers, body=decode_body(_raw_body(message.get('body')), headers))


def _parse_interaction(index: int, entry: Mapping[str, object]) -> Interaction:
    request_raw = entry.get('request')
    response_raw = entry.get('response')
    request = request_raw if isinstance(request_raw, Mapping) else {}
    response = response_raw if isinstance(response_raw, Mapping) else {}

    status = response.get('status')
    code: int | None = None
    message = ''
    if isinstance(status, Mapping):
        try:
            code = int(str(status.get('code')))
        except ValueError:
            code = None
        message = str(status.get('message') or '')

    uri = str(request.get('uri') or '')
    recorded_at = entry.get('recorded_at')
    return Interaction(
        index=index,
        method=str(request.get('method') or '?').upper(),
        uri=uri,
        status_code=code,
        status_message=message,
        request=_parse_message(request),
        response=_parse_message(response),
        recorded_at=str(recorded_at) if recorded_at is not None else None,
        query=tuple(parse_qsl(urlsplit(uri).query, keep_blank_values=True)),
    )


def body_summary(body: Body) -> str:
    """Describe a body in a few words, e.g. 'json, 112 B, gzip-decoded'."""
    if body.kind == 'empty':
        return 'no body'
    return ', '.join((body.kind, human_size(body.size), *body.notes))


def render_text(interaction: Interaction) -> str:
    """Render one interaction as plain text: summary, then each side's headers and body.

    Returns:
        The multi-line rendering.
    """
    lines = [f'{interaction.method} {interaction.uri}', f'-> {interaction.status}']
    if interaction.recorded_at:
        lines.append(f'recorded at {interaction.recorded_at}')
    for title, message in (('Request', interaction.request), ('Response', interaction.response)):
        lines.extend(('', f'== {title} ({body_summary(message.body)}) =='))
        lines.extend(
            f'{name}: {value}' for name, values in message.headers.items() for value in values
        )
        if message.body.kind != 'empty':
            lines.extend(('', message.body.text))
    return '\n'.join(lines)
