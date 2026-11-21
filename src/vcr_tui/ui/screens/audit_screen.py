# Copyright (c) 2026 Kyle King
# SPDX-License-Identifier: MIT
"""Screen summarizing every cassette: hosts, endpoints by status, and findings."""

from pathlib import Path
from typing import ClassVar

from rich.console import Group, RenderableType
from rich.table import Table
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from vcr_tui.preview.audit import AuditReport
from vcr_tui.ui.widgets.preview_panel import status_style

SEVERITY_STYLES = {'error': 'bold red', 'warning': 'yellow', 'info': 'dim'}


def render_audit(report: AuditReport, root: Path) -> Group:
    """Build the rich renderable for a report: totals, hosts, endpoints, findings.

    Returns:
        The grouped tables.
    """
    counts = report.counts()
    summary = Text.assemble(
        (f'{report.cassettes} cassettes, {report.interactions} interactions, ', 'bold'),
        (f'{len(report.hosts)} hosts', 'bold'),
        '   ',
        *(
            part
            for severity, count in counts.items()
            for part in ((f'{count} {severity}', SEVERITY_STYLES[severity]), '  ')
        ),
    )
    parts: list[RenderableType] = [summary]

    if report.hosts:
        hosts = Table(title='Hosts', title_justify='left', expand=False)
        hosts.add_column('Host')
        hosts.add_column('Calls', justify='right')
        for host, count in report.hosts.items():
            hosts.add_row(host, str(count))
        parts.append(hosts)

    if report.endpoints:
        endpoints = Table(title='Endpoints', title_justify='left', expand=True)
        endpoints.add_column('Method', no_wrap=True)
        endpoints.add_column('Endpoint')
        endpoints.add_column('Calls', justify='right')
        endpoints.add_column('Statuses')
        for stats in report.endpoints:
            statuses = Text('  ').join(
                Text(f'{code if code is not None else "-"}x{n}', style=status_style(code))
                for code, n in sorted(stats.statuses.items(), key=lambda kv: kv[0] or 0)
            )
            endpoints.add_row(
                stats.method,
                f'{stats.host}{stats.path}',
                str(stats.count),
                statuses,
            )
        parts.append(endpoints)

    findings = Table(title='Findings', title_justify='left', expand=True)
    findings.add_column('Severity', no_wrap=True)
    findings.add_column('Code', no_wrap=True)
    findings.add_column('Where')
    findings.add_column('What')
    for finding in report.findings:
        findings.add_row(
            Text(finding.severity, style=SEVERITY_STYLES[finding.severity]),
            finding.code,
            finding.location(root),
            finding.message,
        )
    if not report.findings:
        findings.add_row('', '', '', Text('none', style='green'))
    parts.append(findings)
    return Group(*parts)


class AuditScreen(Screen[None]):
    """Read-only report over every cassette the current channel discovers."""

    BINDINGS: ClassVar[list[Binding]] = [
        Binding('escape', 'app.pop_screen', 'Back'),
        Binding('a', 'app.pop_screen', 'Back', show=False),
    ]

    def __init__(self, report: AuditReport, root: Path) -> None:
        """Keep the report and the directory locations are shown relative to."""
        super().__init__()
        self.report = report
        self.root = root

    def compose(self) -> ComposeResult:
        """Lay out the scrolling report between the header and footer.

        Yields:
            The widgets of the audit screen.
        """
        yield Header()
        with VerticalScroll(id='audit-scroll'):
            yield Static(render_audit(self.report, self.root), id='audit-report')
        yield Footer()

    def on_mount(self) -> None:
        """Title the screen with the finding counts."""
        counts = self.report.counts()
        self.sub_title = (
            f'audit: {counts["error"]} error, {counts["warning"]} warning, {counts["info"]} info'
        )
        self.query_one('#audit-scroll').focus()
