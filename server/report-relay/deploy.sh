#!/usr/bin/env bash
# Deploy the report relay to your server over ssh. Safe to re-run.
# Settings come from deploy.env next to this file (not in git):
#   HOST=<ssh host>  DOMAIN=report.example.com  IP=<server public IP>  CHECK="<other urls to check>"
#   bash deploy.sh            service + local smoke test; Caddy only if DNS is ready
# The Telegram token is never passed through here: put TG_TOKEN and TG_CHAT into
# /etc/skill-reports/relay.env on the server, then `systemctl restart skill-reports`.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
[ -f "$DIR/deploy.env" ] || { echo "create $DIR/deploy.env first (see the top of this file)"; exit 2; }
. "$DIR/deploy.env"
: "${HOST:?}" "${DOMAIN:?}" "${IP:?}"

scp -q "$DIR/relay.py" "$DIR/skill-reports.service" "$DIR/report.caddy" "$HOST:/tmp/"
ssh "$HOST" 'export LC_ALL=C.UTF-8; set -e
install -D -m 644 /tmp/relay.py /opt/skill-reports/relay.py
[ -f /etc/skill-reports/relay.env ] || install -m 600 -D /dev/null /etc/skill-reports/relay.env
install -m 644 /tmp/skill-reports.service /etc/systemd/system/skill-reports.service
systemctl daemon-reload
systemctl enable -q skill-reports && systemctl restart skill-reports && sleep 1
echo "service: $(systemctl is-active skill-reports)"
curl -fsS 127.0.0.1:8797/ && echo' 2>&1 | grep -v setlocale

if [ "$(dig +short "$DOMAIN" | tail -1)" != "$IP" ]; then
  echo "DNS: $DOMAIN does not point to $IP yet — add the A record (and no AAAA), then re-run."
  exit 0
fi

ssh "$HOST" 'export LC_ALL=C.UTF-8; set -e
cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.bak-$(date +%F-%H%M)
install -m 644 /tmp/report.caddy /etc/caddy/sites.d/report.caddy
if caddy validate --config /etc/caddy/Caddyfile >/dev/null 2>&1; then
  systemctl reload caddy && echo "caddy: reloaded"
else
  rm /etc/caddy/sites.d/report.caddy; echo "caddy: validate failed, rolled back"; exit 1
fi' 2>&1 | grep -v setlocale

sleep 5
for u in "https://$DOMAIN/" ${CHECK:-}; do
  printf '%-28s %s\n' "$u" "$(curl -s -o /dev/null -w '%{http_code}' "$u")"
done
