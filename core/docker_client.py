"""Docker API wrapper — all docker logic lives here."""
from __future__ import annotations
import requests
import docker as _docker
from docker.models.containers import Container


# ─── Client singleton ─────────────────────────────────────────────────────────

_client: _docker.DockerClient | None = None


def get_client() -> _docker.DockerClient:
    global _client
    if _client is None:
        _client = _docker.from_env()
    return _client


def is_available() -> bool:
    try:
        get_client().ping()
        return True
    except Exception:
        return False


# ─── Container helpers ────────────────────────────────────────────────────────

def list_containers(all_: bool = True) -> list[dict]:
    containers = get_client().containers.list(all=all_)
    result = []
    for c in containers:
        cpu_pct = mem_pct = 0.0
        mem_str = ""
        if c.status == "running":
            try:
                s         = c.stats(stream=False)
                cpu_d     = (s["cpu_stats"]["cpu_usage"]["total_usage"]
                             - s["precpu_stats"]["cpu_usage"]["total_usage"])
                sys_d     = (s["cpu_stats"]["system_cpu_usage"]
                             - s["precpu_stats"]["system_cpu_usage"])
                ncpu      = s["cpu_stats"].get("online_cpus", 1)
                if sys_d > 0:
                    cpu_pct = (cpu_d / sys_d) * ncpu * 100.0
                mem_use   = s["memory_stats"].get("usage", 0)
                mem_lim   = s["memory_stats"].get("limit", 1)
                mem_pct   = (mem_use / mem_lim) * 100
                mem_str   = f"{mem_use/1024**2:.0f} MB / {mem_lim/1024**2:.0f} MB"
            except Exception:
                pass

        ports = []
        if c.ports:
            for k, v in c.ports.items():
                if v:
                    ports.append(f"{v[0]['HostPort']}→{k.split('/')[0]}")

        result.append({
            "id":     c.short_id,
            "name":   c.name,
            "image":  c.image.tags[0] if c.image.tags else c.image.short_id,
            "status": c.status,
            "cpu":    round(cpu_pct, 1),
            "mem":    round(mem_pct, 1),
            "mem_str": mem_str,
            "ports":  ", ".join(ports[:3]),
            "obj":    c,
        })
    return result


def container_action(container_id: str, action: str) -> None:
    c = get_client().containers.get(container_id)
    {"start": c.start, "stop": c.stop, "restart": c.restart}[action]()


def get_logs(container_id: str, tail: int = 200) -> str:
    c = get_client().containers.get(container_id)
    return c.logs(tail=tail).decode("utf-8", errors="replace")


def list_images() -> list[dict]:
    images = get_client().images.list()
    result = []
    for img in images:
        tags = img.tags or [img.short_id]
        result.append({
            "id":   img.short_id,
            "tags": tags,
            "size": f"{img.attrs['Size'] / 1024**2:.0f} MB",
        })
    return result


def pull_image(image: str, tag: str = "latest") -> None:
    """Blocking pull — run in a QThread."""
    get_client().images.pull(image, tag=tag)


# ─── Docker Hub search ────────────────────────────────────────────────────────

def search_hub(query: str, limit: int = 8) -> list[dict]:
    try:
        url = f"https://hub.docker.com/v2/search/repositories/?query={query}&page_size={limit}"
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return [
            {
                "name":        r.get("repo_name", ""),
                "description": r.get("short_description", ""),
                "stars":       r.get("star_count", 0),
                "official":    r.get("is_official", False),
                "pulls":       r.get("pull_count", 0),
            }
            for r in results
        ]
    except Exception:
        return []


# ─── Compose stacks ───────────────────────────────────────────────────────────

import os, subprocess


def list_stacks(base_path: str) -> list[dict]:
    if not os.path.isdir(base_path):
        return []
    result = []
    for name in sorted(os.listdir(base_path)):
        full = os.path.join(base_path, name)
        if not os.path.isdir(full):
            continue
        compose_file = os.path.join(full, "docker-compose.yml")
        has_compose  = os.path.isfile(compose_file)
        result.append({"name": name, "path": full, "has_compose": has_compose})
    return result


def read_compose(stack_path: str) -> str:
    p = os.path.join(stack_path, "docker-compose.yml")
    if os.path.isfile(p):
        with open(p) as f:
            return f.read()
    return ""


def write_compose(stack_path: str, content: str) -> None:
    os.makedirs(stack_path, exist_ok=True)
    with open(os.path.join(stack_path, "docker-compose.yml"), "w") as f:
        f.write(content)


def _compose_run(stack_path: str, args: list[str]) -> tuple[int, str]:
    r = subprocess.run(
        ["docker", "compose"] + args,
        cwd=stack_path, capture_output=True, text=True
    )
    return r.returncode, r.stdout + r.stderr


def compose_up(stack_path: str)      -> tuple[int, str]: return _compose_run(stack_path, ["up", "-d", "--remove-orphans"])
def compose_down(stack_path: str)    -> tuple[int, str]: return _compose_run(stack_path, ["down"])
def compose_pull(stack_path: str)    -> tuple[int, str]: return _compose_run(stack_path, ["pull"])
def compose_restart(stack_path: str) -> tuple[int, str]: return _compose_run(stack_path, ["restart"])
def compose_logs(stack_path: str)    -> tuple[int, str]: return _compose_run(stack_path, ["logs", "--tail=200", "--no-color"])