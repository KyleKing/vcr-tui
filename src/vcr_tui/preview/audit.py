# Copyright (c) 2026 Kyle King
# SPDX-License-Identifier: MIT
"""Summarize and audit every recorded interaction across a test suite's cassettes.

Pure functions over parsed cassettes: no UI imports and no YAML loading, so the
report is the same whether the CLI prints it or the TUI renders it.
"""

import re
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from vcr_tui.preview.cassette import Body, HttpMessage, Interaction, human_size

Severity = Literal['error', 'warning', 'info']
SEVERITY_RANK: dict[str, int] = {'info': 0, 'warning': 1, 'error': 2}
DEFAULT_MAX_BODY_BYTES = 100 * 1024
_SERVER_ERROR = 500

_SENSITIVE_HEADERS = frozenset({
    'authorization',
    'proxy-authorization',
    'cookie',
    'x-api-key',
    'api-key',
    'x-auth-token',
    'x-access-token',
})
_SENSITIVE_HEADER_WORDS = ('token', 'secret', 'api-key', 'apikey', 'password')
_SENSITIVE_QUERY = frozenset({
    'access_token',
    'api_key',
    'apikey',
    'auth',
    'client_secret',
    'password',
    'secret',
    'token',
})
_SENSITIVE_FIELDS = (
    r'password|passwd|client_secret|access_token|refresh_token|api_key|apikey|secret'
)
_FIELD_PATTERNS = (
    re.compile(rf'"({_SENSITIVE_FIELDS})"\s*:\s*"([^"]*)"', re.IGNORECASE),
    re.compile(rf'^({_SENSITIVE_FIELDS}) = (.*)$', re.IGNORECASE | re.MULTILINE),
)
_TOKEN_PATTERNS = (
    ('JWT', re.compile(r'eyJ[\w-]{8,}\.eyJ[\w-]{8,}\.[\w-]{8,}')),
    ('AWS access key', re.compile(r'\bAKIA[0-9A-Z]{16}\b')),
    ('GitHub token', re.compile(r'\bgh[pousr]_[A-Za-z0-9]{30,}\b')),
    ('Slack token', re.compile(r'\bxox[abprs]-[A-Za-z0-9-]{10,}')),
    ('private key', re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----')),
)
_EMAIL = re.compile(r'\b[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}\b')
_REDACTED = re.compile(
    r'^(|\*+|x+|-+|none|null|redacted|filtered|dummy|fake|test|secret|<[^>]*>|\[[^\]]*\]'
    r'|\{\{[^}]*\}\})$',
)
_AUTH_SCHEME = re.compile(r'^(bearer|basic|token|digest)\s+', re.IGNORECASE)
_ID_SEGMENT = re.compile(
    r'^(\d+|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|[0-9a-f]{12,})$',
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Cassette:
    """One cassette file and the interactions parsed from it."""

    path: Path
    interactions: tuple[Interaction, ...]


@dataclass(frozen=True)
class Finding:
    """Something worth a reviewer's attention, located in one cassette."""

    severity: Severity
    code: str
    path: Path
    message: str
    index: int | None = None

    def location(self, root: Path) -> str:
        """The cassette path relative to root, plus '#index' for an interaction."""
        try:
            shown = self.path.relative_to(root)
        except ValueError:
            shown = self.path
        return f'{shown}#{self.index}' if self.index is not None else str(shown)


@dataclass(frozen=True)
class EndpointStats:
    """How often one method + templated path was recorded, by status code."""

    method: str
    host: str
    path: str
    statuses: dict[int | None, int]

    @property
    def count(self) -> int:
        """Total recorded calls to this endpoint."""
        return sum(self.statuses.values())


@dataclass(frozen=True)
class AuditOptions:
    """Knobs for the checks: body size limit, test lookup, and codes to skip."""

    max_body_bytes: int = DEFAULT_MAX_BODY_BYTES
    check_tests: bool = True
    skip: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class AuditReport:
    """Suite-wide totals, per-host and per-endpoint counts, and findings."""

    cassettes: int
    interactions: int
    hosts: dict[str, int]
    endpoints: list[EndpointStats]
    findings: list[Finding]

    def counts(self) -> dict[str, int]:
        """Number of findings per severity, every severity present."""
        tally = Counter(f.severity for f in self.findings)
        return {severity: tally.get(severity, 0) for severity in ('error', 'warning', 'info')}

    def failed(self, threshold: str) -> bool:
        """Whether any finding is at or above the severity threshold ('never' never fails)."""
        if threshold not in SEVERITY_RANK:
            return False
        floor = SEVERITY_RANK[threshold]
        return any(SEVERITY_RANK[f.severity] >= floor for f in self.findings)


def template_path(path: str) -> str:
    """Collapse id-like path segments to '{id}' and drop the query string.

    So ``/users/1`` and ``/users/42?x=1`` both count toward ``/users/{id}``.
    """
    bare = path.split('?', 1)[0] or '/'
    segments = ['{id}' if _ID_SEGMENT.match(seg) else seg for seg in bare.split('/')]
    return '/'.join(segments) or '/'


def is_redacted(value: str) -> bool:
    """Whether a recorded secret value looks scrubbed (empty, '***', 'REDACTED', ...)."""
    bare = _AUTH_SCHEME.sub('', value.strip()).strip().casefold()
    return bool(_REDACTED.match(bare)) or 'redacted' in bare or 'filtered' in bare


def find_test(cassette_path: Path) -> bool | None:
    """Look for the test that recorded a cassette, by pytest-recording's naming.

    pytest-recording writes ``<dir>/cassettes/<module>/<test>.yaml`` beside
    ``<dir>/<module>.py``; class tests are ``<Class>.<test>`` and parametrized
    ones keep their ``[id]`` suffix. Other layouts fall back to every module
    directly in ``<dir>``.

    Returns:
        True when a matching ``def`` exists, False when none does, and None
        when the cassette does not follow a test-named layout at all.
    """
    parts = cassette_path.parts
    if 'cassettes' not in parts[:-1]:
        return None
    position = len(parts) - 1 - parts[::-1].index('cassettes')
    name = cassette_path.stem.split('[', 1)[0].rsplit('.', 1)[-1]
    if not name.startswith('test'):
        return None

    root = Path(*parts[:position])
    between = parts[position + 1 : -1]
    candidates: list[Path] = []
    if between:
        candidates.append(root.joinpath(*between[:-1], f'{between[-1]}.py'))
    candidates.extend(sorted(root.glob('*.py')))

    definition = re.compile(rf'^\s*(?:async\s+)?def\s+{re.escape(name)}\s*\(', re.MULTILINE)
    for candidate in dict.fromkeys(candidates):
        if candidate.is_file() and definition.search(
            candidate.read_text(encoding='utf-8', errors='replace'),
        ):
            return True
    return False


def audit(
    cassettes: Sequence[Cassette],
    options: AuditOptions | None = None,
    unreadable: Iterable[tuple[Path, str]] = (),
) -> AuditReport:
    """Summarize the cassettes and collect findings.

    Returns:
        The report, with findings sorted most severe first, then by location.
    """
    options = options or AuditOptions()
    hosts: Counter[str] = Counter()
    endpoints: dict[tuple[str, str, str], Counter[int | None]] = {}
    findings = [
        Finding('warning', 'unreadable', path, f'could not be parsed: {reason}')
        for path, reason in unreadable
    ]

    for cassette in cassettes:
        findings.extend(_cassette_findings(cassette, options))
        for interaction in cassette.interactions:
            hosts[interaction.host or '(no host)'] += 1
            key = (interaction.method, interaction.host, template_path(interaction.path))
            endpoints.setdefault(key, Counter())[interaction.status_code] += 1
            findings.extend(_interaction_findings(cassette.path, interaction, options))

    kept = [f for f in findings if f.code not in options.skip]
    kept.sort(
        key=lambda f: (
            -SEVERITY_RANK[f.severity],
            str(f.path),
            -1 if f.index is None else f.index,
            f.code,
        ),
    )
    stats = [
        EndpointStats(method, host, path, dict(statuses))
        for (method, host, path), statuses in endpoints.items()
    ]
    stats.sort(key=lambda s: (-s.count, s.host, s.path, s.method))
    return AuditReport(
        cassettes=len(cassettes),
        interactions=sum(len(c.interactions) for c in cassettes),
        hosts=dict(hosts.most_common()),
        endpoints=stats,
        findings=kept,
    )


def _cassette_findings(cassette: Cassette, options: AuditOptions) -> list[Finding]:
    path = cassette.path
    findings: list[Finding] = []
    if not cassette.interactions:
        findings.append(Finding('warning', 'empty-cassette', path, 'records no interactions'))
    if options.check_tests and 'no-test' not in options.skip and find_test(path) is False:
        findings.append(
            Finding('warning', 'no-test', path, f'no test named {path.stem!r} was found'),
        )

    seen: dict[tuple[str, str, str], list[int]] = {}
    for interaction in cassette.interactions:
        key = (interaction.method, interaction.uri, interaction.request.body.text)
        seen.setdefault(key, []).append(interaction.index)
    for (method, uri, _body), indexes in seen.items():
        if len(indexes) > 1:
            where = ', '.join(map(str, indexes))
            findings.append(
                Finding(
                    'info',
                    'duplicate',
                    path,
                    f'{method} {uri} recorded {len(indexes)} times (#{where})',
                    indexes[0],
                ),
            )
    return findings


def _interaction_findings(
    path: Path,
    interaction: Interaction,
    options: AuditOptions,
) -> list[Finding]:
    index = interaction.index
    findings = [
        Finding(severity, code, path, message, index)
        for severity, code, message in _secret_findings(interaction)
    ]
    size = interaction.response.body.size
    if size > options.max_body_bytes:
        limit = human_size(options.max_body_bytes)
        findings.append(
            Finding(
                'warning',
                'large-body',
                path,
                f'response body is {human_size(size)} (limit {limit})',
                index,
            ),
        )
    if interaction.status_code is not None and interaction.status_code >= _SERVER_ERROR:
        findings.append(
            Finding('info', 'server-error', path, f'recorded a {interaction.status}', index),
        )
    return findings


def _secret_findings(interaction: Interaction) -> list[tuple[Severity, str, str]]:
    found: list[tuple[Severity, str, str]] = []
    for name, values in interaction.request.headers.items():
        lowered = name.casefold()
        sensitive = lowered in _SENSITIVE_HEADERS or any(
            word in lowered for word in _SENSITIVE_HEADER_WORDS
        )
        if sensitive and any(not is_redacted(value) for value in values):
            found.append(('error', 'secret-header', f'request header {name} is not redacted'))
    if any(name.casefold() == 'set-cookie' for name in interaction.response.headers):
        found.append(('warning', 'set-cookie', 'response sets a cookie'))
    for name, value in interaction.query:
        if name.casefold() in _SENSITIVE_QUERY and not is_redacted(value):
            found.append(('error', 'secret-query', f'query parameter {name} is not redacted'))
    for side, message in (('request', interaction.request), ('response', interaction.response)):
        found.extend(_body_secret_findings(side, message))
    return found


def _body_secret_findings(side: str, message: HttpMessage) -> list[tuple[Severity, str, str]]:
    body: Body = message.body
    if body.kind in {'empty', 'binary'}:
        return []
    found: list[tuple[Severity, str, str]] = []
    fields = sorted({
        match.group(1)
        for pattern in _FIELD_PATTERNS
        for match in pattern.finditer(body.text)
        if not is_redacted(match.group(2))
    })
    if fields:
        found.append((
            'error',
            'secret-field',
            f'{side} body has unredacted {", ".join(fields)}',
        ))
    for label, pattern in _TOKEN_PATTERNS:
        if pattern.search(body.text):
            found.append(('error', 'secret-token', f'{side} body contains a {label}'))
    emails = set(_EMAIL.findall(body.text))
    if emails:
        found.append(('info', 'email', f'{side} body contains {len(emails)} email address(es)'))
    return found


def render_report(report: AuditReport, root: Path) -> str:
    """Render the report as plain text for the CLI.

    Returns:
        The multi-line report.
    """
    lines = [
        f'{report.cassettes} cassettes, {report.interactions} interactions, '
        f'{len(report.hosts)} hosts',
    ]
    if report.hosts:
        lines.extend(('', 'Hosts'))
        width = max(map(len, report.hosts))
        lines.extend(f'  {host:<{width}}  {count}' for host, count in report.hosts.items())
    if report.endpoints:
        lines.extend(('', 'Endpoints'))
        width = max(len(f'{s.host}{s.path}') for s in report.endpoints)
        for stats in report.endpoints:
            statuses = '  '.join(
                f'{code if code is not None else "-"}x{count}'
                for code, count in sorted(stats.statuses.items(), key=lambda kv: kv[0] or 0)
            )
            target = f'{stats.host}{stats.path}'
            lines.append(f'  {stats.method:<7} {target:<{width}}  {statuses}')
    counts = report.counts()
    summary = ', '.join(f'{count} {severity}' for severity, count in counts.items())
    lines.extend(('', f'Findings ({summary})'))
    if not report.findings:
        lines.append('  none')
    lines.extend(
        f'  {f.severity:<7}  {f.code:<14}  {f.location(root)}  {f.message}'
        for f in report.findings
    )
    return '\n'.join(lines)


def report_to_dict(report: AuditReport, root: Path) -> dict[str, object]:
    """Convert the report to JSON-ready data for the CLI's --format json.

    Returns:
        Plain dicts, lists, strings, and numbers.
    """
    return {
        'cassettes': report.cassettes,
        'interactions': report.interactions,
        'hosts': report.hosts,
        'endpoints': [
            {
                'method': s.method,
                'host': s.host,
                'path': s.path,
                'count': s.count,
                'statuses': {str(code): n for code, n in s.statuses.items()},
            }
            for s in report.endpoints
        ],
        'counts': report.counts(),
        'findings': [
            {
                'severity': f.severity,
                'code': f.code,
                'location': f.location(root),
                'index': f.index,
                'message': f.message,
            }
            for f in report.findings
        ],
    }
