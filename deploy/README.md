# Deployment (Docker)

This project is deployed via Docker Compose on a host that already runs two
other Next.js projects (`finclaw` on port 3000, `notememo` on port 3001) behind
a system nginx. Docker is **scoped to this project only** and does not touch
those services.

## Port allocation on the host

| Service          | Host port        | Owner             |
|------------------|------------------|-------------------|
| finclaw          | 3000             | pm2 (native node) |
| notememo         | 3001             | pm2 (native node) |
| **stockpredict** | **3002 (lo)**    | docker compose    |

`stockpredict` is only bound to `127.0.0.1:3002`, so it is invisible to the
internet until the host nginx adds a reverse proxy (see
`nginx.stockpredict.example.conf`).

## Prerequisites

Docker is not installed yet. Install once:

```bash
curl -fsSL https://get.docker.com | sh
# compose v2 plugin is included with modern docker-ce
docker --version
docker compose version
```

## Configure environment

```bash
cd /root/project/stock-predict
cp .env.example .env
# then edit .env and fill in API keys etc.
```

`DATABASE_URL`, `CACHE_DIR`, `REPORTS_DIR` are overridden in compose to point
at volume-mounted paths, so you don't need to change those in `.env`.

## Build and start

```bash
cd /root/project/stock-predict
docker compose build
docker compose up -d
docker compose logs -f stockpredict
```

Smoke test (still only reachable from the host):

```bash
curl -I http://127.0.0.1:3002/
curl    http://127.0.0.1:3002/docs
```

## Hook up nginx (when ready)

1. Point a DNS record at this server for your chosen domain.
2. Issue a certificate (e.g. `certbot certonly --nginx -d stock.example.com`).
3. Copy `deploy/nginx.stockpredict.example.conf` to
   `/etc/nginx/sites-available/stockpredict`, edit `server_name` and cert
   paths.
4. `ln -s ../sites-available/stockpredict /etc/nginx/sites-enabled/stockpredict`
5. `nginx -t && systemctl reload nginx`

The existing `finclaw` and `notememo.ai` site files are untouched.

## Updating

```bash
cd /root/project/stock-predict
git pull
docker compose build
docker compose up -d
```

## Data persistence

The following host dirs are bind-mounted into the container and survive
rebuilds:

- `./data`    — sqlite database (`stockpredict.db`)
- `./cache`   — parquet/json caches
- `./reports` — exported JSON reports
- `./models`  — ML model artifacts

Back these up, not the image.

## Stopping / removing

```bash
docker compose down           # stop container, keep volumes
docker compose down --rmi all # also remove the image
```
