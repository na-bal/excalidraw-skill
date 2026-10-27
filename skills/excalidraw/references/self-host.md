# Your own board server — short version

For the agent: walk the user through this step by step, one step at a time. Ask
what they already have (a VPS? a domain? Docker?) and skip what's done. Details
beyond this list — in the ExcaliDash README; figure them out with the user.

**What it is.** [ExcaliDash](https://github.com/ZimengXiong/ExcaliDash): Excalidraw
on your own server with named boards, login, version history, sharing and API
keys. The skill is tested with 0.6.0.

**What's needed.** A VPS with 1 CPU and 1 GB RAM, Docker, a domain or subdomain.

**Steps.**
1. DNS: an A record for the subdomain → the server's IP. Check the whole zone:
   some registrar panels add extra A/AAAA records on their own, and a stray AAAA
   breaks the Let's Encrypt certificate.
2. Install ExcaliDash with Docker Compose following its README.
3. Before the first start, set in the backend environment:
   - `AUTH_MODE=local`, `NODE_ENV=production`;
   - `JWT_SECRET` and `API_KEY_HASH_PEPPER` — long random strings
     (`openssl rand -hex 32`). The pepper must be set before the first API key:
     changing it later breaks every issued key;
   - `TRUST_PROXY` = number of proxies in front of the backend. With Caddy/nginx
     on the host plus the nginx inside the frontend container it's `2`; with `1`
     the login limiter treats everyone as one client and locks everybody out.
4. HTTPS: a reverse proxy on the host, e.g. Caddy:
   `draw.example.com { reverse_proxy 127.0.0.1:<frontend port> }`.
5. Open the site, create the admin account, then Settings → API keys → new key.
6. The user runs in their own terminal (the key never goes through the chat):
   `bash SKILL_DIR/scripts/setup.sh --backend excalidash --url https://draw.example.com`

**Good to know.**
- Small VPS shared with other services: give the containers a `mem_limit`.
- Login via Google/OIDC: set `OIDC_JIT_PROVISIONING=false`, otherwise any account
  that passes the identity provider gets a user on the server.
- Several people on one server: registration is closed by default — keep it so,
  the admin creates accounts. API keys are isolated per user, but the share
  dialog lets any user find others by part of their email or name. If users
  shouldn't know each other, give them neutral logins (e.g. `anna@boards.local`)
  or run one instance per person.
- The admin can see everything (impersonation) — say so to the people you host.

**Don't want to run a server?** The skill's author hosts boards: Telegram
[@Ohio_blue_tip](https://t.me/Ohio_blue_tip) or bdlv@bdlv.me.
