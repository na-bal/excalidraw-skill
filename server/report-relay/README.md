# Report relay

What the skill's `scripts/report.py` sends when the user agrees to report a
problem to the author. A tiny stdlib Python service: checks the schema, size and
rate, stores the report and forwards it to the author's Telegram.

What a report contains: kind, title, the text the user saw and approved, skill
version, OS, Python/Node versions, agent name. Never board contents or keys —
`report.py` strips home paths and anything that looks like a token before showing
the draft to the user.

Deploy (Linux, systemd, Caddy):

```sh
install -D relay.py /opt/skill-reports/relay.py
install -m 600 -D /dev/null /etc/skill-reports/relay.env   # TG_TOKEN=… TG_CHAT=…
cp skill-reports.service /etc/systemd/system/ && systemctl enable --now skill-reports
cp report.caddy /etc/caddy/sites.d/ && caddy validate --config /etc/caddy/Caddyfile && systemctl reload caddy
```

Mute Telegram without losing reports: `touch /var/lib/skill-reports/muted`.
