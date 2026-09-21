# FlexMix Hub — Phase 00 foundation

This repository currently contains only the Hub project foundation: a FastAPI
process, local MySQL development container, SQLAlchemy session foundation,
Alembic baseline and tests. It contains no Hub business schema and no machine
backend, agent, authentication, sync, event, command, payment, inventory,
backup or release implementation.

The source-of-truth remains [`docs/AI_CONTEXT.md`](docs/AI_CONTEXT.md) and its
linked specifications. This implementation does not accept any DRAFT decision
or close an open question.

## Local setup

The checked development baseline is Python 3.12 and the existing local image
`mysql:8.4.11`. It is a reproducible development choice only; Q-24 remains open
for officially supported versions and packaging.

Install Python's `venv` package if it is unavailable on the host, then create
and install the environment:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[dev]'
```

Create password files outside the repository and restrict their permissions.
The following commands never print the generated values:

```bash
install -d -m 700 /tmp/flexmix-foundation-secrets
umask 077
openssl rand -base64 32 > /tmp/flexmix-foundation-secrets/mysql-app-password
openssl rand -base64 32 > /tmp/flexmix-foundation-secrets/mysql-root-password
```

Copy the example to `.env` and provide non-secret local database names and the
two absolute file paths:

```bash
cp config/examples/development.env.example .env
```

Required values are `FLEXMIX_DB_NAME`, `FLEXMIX_DB_USER`,
`FLEXMIX_DB_PASSWORD_FILE`, and `MYSQL_ROOT_PASSWORD_FILE`. The app consumes
only `FLEXMIX_*`; the root password exists solely for MySQL initialization.

Dashboard login uses `FLEXMIX_ADMIN_USERNAME` and an Argon2 hash in
`FLEXMIX_ADMIN_PASSWORD_HASH` (generate one with
`.venv/bin/python -c 'from argon2 import PasswordHasher; print(PasswordHasher().hash(input()))'`).
Keep the hash out of logs and source control.

## Phase 01 prototype enrollment

The prototype registry has a separate bootstrap token, stored outside the
repository like the database passwords. It is not mTLS or Ed25519 request
authentication; those production details remain Q-12/Q-15.

```bash
umask 077
openssl rand -base64 32 > /tmp/flexmix-foundation-secrets/enrollment-token
```

Set `FLEXMIX_PROTOTYPE_ENROLLMENT_TOKEN_FILE` in `.env` to that absolute path.
The prototype endpoints are intentionally named `/v1/prototype/fleet/*` and
return a non-secret `fleet.env` handoff template. The device must generate and
retain its own private key. Use
[`config/examples/tailscale-acl-prototype.hujson`](config/examples/tailscale-acl-prototype.hujson)
only as a dedicated-tailnet template; it does not configure Tailscale itself.

## Run and verify

```bash
docker compose up -d --wait
.venv/bin/alembic upgrade head
.venv/bin/alembic current
.venv/bin/alembic check
FLEXMIX_TEST_MYSQL=1 .venv/bin/pytest
.venv/bin/uvicorn flexmix_hub.main:create_app --factory --host 127.0.0.1 --port 8010
curl http://127.0.0.1:8010/health
curl http://127.0.0.1:8010/health/ready
```

`/health` is process liveness. `/health/ready` performs `SELECT 1` against the
development database and returns HTTP 503 with no connection details if it is
unavailable. The initial Alembic revision creates no business tables; it only
establishes the migration baseline (`0001_foundation`).

Stop the isolated development database with:

```bash
docker compose down
```

Use `docker compose down -v` only when intentionally discarding the local
development database volume.

## Internet access through HTTPS reverse proxy

Keep the Hub bound to `127.0.0.1:8010`; never publish port 8010 publicly. Copy
[`deploy/nginx/flexmix-hub.conf.example`](deploy/nginx/flexmix-hub.conf.example)
to the Nginx site configuration and replace the example domain and certificate
paths. This project cannot create your DNS record or issue a certificate.

After DNS points your domain to the server and its certificate is installed:

```bash
sudo cp deploy/nginx/flexmix-hub.conf.example /etc/nginx/sites-available/flexmix-hub
sudo ln -s /etc/nginx/sites-available/flexmix-hub /etc/nginx/sites-enabled/flexmix-hub
sudo nginx -t && sudo systemctl reload nginx
```

The optional systemd template is
[`deploy/systemd/flexmix-hub.service.example`](deploy/systemd/flexmix-hub.service.example).
It runs Uvicorn on localhost only and trusts forwarded headers only from the
local proxy. Check with `ss -ltnp | grep ':8010'` and
`curl -fsS http://127.0.0.1:8010/health`.

From another network, open `https://flexmix.example.com/login`, sign in with
the configured Admin credentials, verify Dashboard, then Logout and confirm
that `/` redirects to `/login`. HTTP must redirect to HTTPS. Machine APIs are
proxied unchanged; enrollment tokens remain header-only credentials.
