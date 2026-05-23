#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRAPYD_DIR="$ROOT_DIR/TLNewsSpider/scrapyd_server"
SCRAPYDWEB_DIR="$ROOT_DIR/TLNewsSpider/scrapyd_web_manager"
VENV_DIR="${NEWSCRAWL_VENV_DIR:-$ROOT_DIR/.venv}"
LOG_DIR="$ROOT_DIR/logs"
DATA_DIR="$ROOT_DIR/data"
SQLITE_PATH="${NEWSCRAWL_SQLITE_PATH:-$DATA_DIR/news_crawl.sqlite3}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

usage() {
    cat <<'EOF'
NewsCrawl one-key startup

Usage:
  ./start.sh quick             本地快速启动：SQLite + 关闭 Redis 去重 + scrapyd/scrapydweb
  ./start.sh full              完整 Docker 部署：MySQL + Redis + scrapyd + scrapydweb
  ./start.sh stop              停止 quick/full 启动的服务
  ./start.sh status            查看服务状态
  ./start.sh logs [service]    查看日志：scrapyd|scrapydweb|docker

Environment:
  NEWSCRAWL_MYSQL_PASSWORD     完整部署 MySQL root 密码，默认 Tlrobot123.
  NEWSCRAWL_SQLITE_PATH        快速启动 SQLite 文件路径，默认 ./data/news_crawl.sqlite3
  NEWSCRAWL_INSTALL_DEPS=0     快速启动时跳过 pip 依赖安装
EOF
}

log() {
    printf '[NewsCrawl] %s\n' "$*"
}

has_cmd() {
    command -v "$1" >/dev/null 2>&1
}

compose_cmd() {
    if docker compose version >/dev/null 2>&1; then
        echo "docker compose"
    elif has_cmd docker-compose; then
        echo "docker-compose"
    else
        echo ""
    fi
}

prepare_dirs() {
    mkdir -p "$LOG_DIR" "$DATA_DIR"
    mkdir -p "$SCRAPYD_DIR/logs"
}

prepare_venv() {
    if [ ! -x "$VENV_DIR/bin/python" ]; then
        log "创建虚拟环境：$VENV_DIR"
        "$PYTHON_BIN" -m venv "$VENV_DIR"
    fi

    if [ "${NEWSCRAWL_INSTALL_DEPS:-1}" != "0" ]; then
        log "安装/校验 Python 依赖"
        "$VENV_DIR/bin/python" -m pip install --upgrade pip
        # demjson==2.2.4 依赖 setuptools 的 use_2to3，需使用旧 setuptools 构建。
        "$VENV_DIR/bin/python" -m pip install "setuptools<58" wheel
        "$VENV_DIR/bin/python" -m pip install --no-build-isolation --no-use-pep517 -r "$ROOT_DIR/docker_yml/news_crawl/requirements.txt"
    fi
}

start_quick() {
    prepare_dirs
    prepare_venv

    export NEWSCRAWL_DB_BACKEND=sqlite
    export NEWSCRAWL_ROOT="$ROOT_DIR"
    export NEWSCRAWL_SQLITE_PATH="$SQLITE_PATH"
    export NEWSCRAWL_REDIS_ENABLED=0
    export NEWSCRAWL_STORAGE_ENABLED=1
    export NEWSCRAWL_SCRAPYDWEB_DATA_PATH="$DATA_DIR/scrapydweb"
    export PYTHONPATH="$ROOT_DIR/TLNewsSpider:${PYTHONPATH:-}"

    log "快速启动使用 SQLite：$SQLITE_PATH"

    if [ -f "$SCRAPYD_DIR/scrapyd.pid" ] && kill -0 "$(cat "$SCRAPYD_DIR/scrapyd.pid")" >/dev/null 2>&1; then
        log "scrapyd 已在运行"
    else
        (cd "$SCRAPYD_DIR"; nohup "$VENV_DIR/bin/scrapyd" --pidfile= > "$LOG_DIR/scrapyd.log" 2>&1 & echo $! > scrapyd.pid)
        log "scrapyd 已启动：http://127.0.0.1:6800"
    fi

    if [ -f "$SCRAPYDWEB_DIR/scrapydweb.pid" ] && kill -0 "$(cat "$SCRAPYDWEB_DIR/scrapydweb.pid")" >/dev/null 2>&1; then
        log "scrapydweb 已在运行"
    else
        (cd "$SCRAPYDWEB_DIR"; nohup "$VENV_DIR/bin/scrapydweb" > "$LOG_DIR/scrapydweb.log" 2>&1 & echo $! > scrapydweb.pid)
        log "scrapydweb 已启动：http://127.0.0.1:5000"
    fi

    wait_for_services
}

prepare_database_mounts() {
    mkdir -p "$ROOT_DIR/docker_yml/database/mysql57/log"
    mkdir -p "$ROOT_DIR/docker_yml/database/mysql57/data"
    mkdir -p "$ROOT_DIR/docker_yml/database/redis/data"
    mkdir -p "$ROOT_DIR/docker_yml/database/redis/log"
    touch "$ROOT_DIR/docker_yml/database/redis/log/redis.log"
}

start_full() {
    local compose
    compose="$(compose_cmd)"
    if [ -z "$compose" ]; then
        log "未找到 docker compose 或 docker-compose，无法执行完整部署"
        exit 1
    fi

    prepare_database_mounts
    export NEWSCRAWL_ROOT="$ROOT_DIR"
    export NEWSCRAWL_MYSQL_PASSWORD="${NEWSCRAWL_MYSQL_PASSWORD:-Tlrobot123.}"

    log "完整部署启动 MySQL、Redis、scrapyd、scrapydweb"
    $compose \
        -f "$ROOT_DIR/docker_yml/database/docker-compose.yml" \
        -f "$ROOT_DIR/docker_yml/news_crawl/docker-compose.yml" \
        up -d --build

    wait_for_services
}

stop_quick() {
    for item in "$SCRAPYD_DIR/scrapyd.pid" "$SCRAPYDWEB_DIR/scrapydweb.pid"; do
        if [ -f "$item" ]; then
            pid="$(cat "$item")"
            if kill -0 "$pid" >/dev/null 2>&1; then
                log "停止进程：$pid"
                kill "$pid" || true
            fi
            rm -f "$item"
        fi
    done
}

stop_full() {
    local compose
    compose="$(compose_cmd)"
    if [ -n "$compose" ]; then
        export NEWSCRAWL_ROOT="$ROOT_DIR"
        $compose \
            -f "$ROOT_DIR/docker_yml/database/docker-compose.yml" \
            -f "$ROOT_DIR/docker_yml/news_crawl/docker-compose.yml" \
            down
    fi
}

stop_all() {
    stop_quick
    stop_full
}

check_url() {
    local name="$1"
    local url="$2"
    if has_cmd curl && curl -fsS --max-time 2 "$url" >/dev/null 2>&1; then
        log "$name 正常：$url"
    else
        log "$name 未确认：$url"
    fi
}

wait_for_url() {
    local name="$1"
    local url="$2"
    local max_seconds="${3:-30}"
    local elapsed=0

    if ! has_cmd curl; then
        log "未找到 curl，跳过 $name 健康检查"
        return 0
    fi

    while [ "$elapsed" -lt "$max_seconds" ]; do
        if curl -fsS --max-time 2 "$url" >/dev/null 2>&1; then
            log "$name 正常：$url"
            return 0
        fi
        sleep 1
        elapsed=$((elapsed + 1))
    done

    log "$name 启动超时：$url"
    return 1
}

wait_for_services() {
    wait_for_url "scrapyd" "http://127.0.0.1:6800/daemonstatus.json" 30
    wait_for_url "scrapydweb" "http://127.0.0.1:5000" 30
}

status() {
    check_url "scrapyd" "http://127.0.0.1:6800/daemonstatus.json"
    check_url "scrapydweb" "http://127.0.0.1:5000"
}

show_logs() {
    case "${1:-scrapyd}" in
        scrapyd)
            tail -200f "$LOG_DIR/scrapyd.log"
            ;;
        scrapydweb)
            tail -200f "$LOG_DIR/scrapydweb.log"
            ;;
        docker)
            compose="$(compose_cmd)"
            if [ -z "$compose" ]; then
                log "未找到 docker compose 或 docker-compose"
                exit 1
            fi
            export NEWSCRAWL_ROOT="$ROOT_DIR"
            $compose \
                -f "$ROOT_DIR/docker_yml/database/docker-compose.yml" \
                -f "$ROOT_DIR/docker_yml/news_crawl/docker-compose.yml" \
                logs -f
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

case "${1:-}" in
    quick)
        start_quick
        ;;
    full)
        start_full
        ;;
    stop)
        stop_all
        ;;
    status)
        status
        ;;
    logs)
        show_logs "${2:-scrapyd}"
        ;;
    -h|--help|help|"")
        usage
        ;;
    *)
        usage
        exit 1
        ;;
esac
