#!/usr/bin/env bash
# Start / restart the stockpredict backend + frontend via docker compose.
#
# Usage:
#   ./scripts/start.sh           # start (rebuild if code changed)
#   ./scripts/start.sh --rebuild # force rebuild image
#   ./scripts/start.sh --logs    # follow logs after starting
#   ./scripts/start.sh stop      # stop the container
#   ./scripts/start.sh restart   # restart without rebuild
#   ./scripts/start.sh status    # show container status

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

SERVICE="stockpredict"
PORT="3002"

cmd="${1:-up}"

case "$cmd" in
  up|start|"")
    echo "==> Building & starting $SERVICE (compose up -d --build)"
    docker compose up -d --build
    ;;
  --rebuild|rebuild)
    echo "==> Forcing full rebuild (no cache)"
    docker compose build --no-cache
    docker compose up -d
    ;;
  --logs|logs)
    docker compose up -d --build
    docker compose logs -f "$SERVICE"
    exit 0
    ;;
  stop|down)
    echo "==> Stopping $SERVICE"
    docker compose down
    exit 0
    ;;
  restart)
    echo "==> Restarting $SERVICE (no rebuild)"
    docker compose restart "$SERVICE"
    ;;
  status)
    docker compose ps
    exit 0
    ;;
  *)
    echo "Unknown command: $cmd" >&2
    echo "Usage: $0 [up|rebuild|logs|stop|restart|status]" >&2
    exit 1
    ;;
esac

echo
echo "==> Status:"
docker compose ps
echo
echo "Backend (loopback):  http://127.0.0.1:${PORT}"
echo "API docs:            http://127.0.0.1:${PORT}/docs"
echo "Public site:         served via host nginx reverse-proxy"
echo
echo "Tail logs:  docker compose logs -f $SERVICE"
