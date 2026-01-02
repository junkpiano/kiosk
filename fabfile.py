from __future__ import annotations

from io import StringIO
from pathlib import PurePosixPath

from fabric import Connection, task


RSYNC_EXCLUDES = [
    ".git/",
    ".DS_Store",
    "__pycache__/",
    "*.pyc",
    ".venv/",
    "venv/",
    "*.md",
    "deploy.sh",
    "*.png",
    "LICENSE",
    "frontend/node_modules/",
    "frontend/.svelte-kit/",
    "frontend/.vite/",
    "frontend/.cache/",
]


def _rsync_exclude_args() -> str:
    return " ".join(f'--exclude "{pattern}"' for pattern in RSYNC_EXCLUDES)


def _remote_home(c: Connection) -> str:
    return c.run('printf "%s" "$HOME"', hide=True).stdout.strip()


def _service_unit(remote_dir: str, service_user: str, home_dir: str) -> str:
    workdir = PurePosixPath(remote_dir)
    path = ":".join(
        [
            f"{home_dir}/.local/bin",
            "/usr/sbin",
            "/usr/local/bin",
            "/usr/bin",
            "/bin",
        ]
    )
    return f"""[Unit]
Description=Kiosk Dashboard
After=network.target

[Service]
Type=simple
User={service_user}
WorkingDirectory={workdir}
Environment=PATH={path}
ExecStartPre=-/usr/bin/env fuser -k 8080/tcp
ExecStart=/usr/bin/env uv run uvicorn main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""


def _expand_remote_dir(c: Connection, remote_dir: str) -> str:
    if remote_dir.startswith("~"):
        home = _remote_home(c)
        return remote_dir.replace("~", home, 1)
    return remote_dir


@task
def sync(c: Connection, remote_dir: str = "~/kiosk_dashboard") -> None:
    exclude_args = _rsync_exclude_args()
    c.local(
        f'rsync -avz --delete {exclude_args} ./ "{c.host}:{remote_dir}/"'
    )

@task
def ensure_uv(c: Connection) -> None:
    if c.run("command -v uv", hide=True, warn=True).exited == 0:
        return
    c.run("curl -LsSf https://astral.sh/uv/install.sh | sh")

@task
def uv_sync(c: Connection, remote_dir: str = "~/kiosk_dashboard") -> None:
    home_dir = _remote_home(c)
    with c.cd(remote_dir):
        c.run(f'PATH="{home_dir}/.local/bin:$PATH" uv sync')


@task
def install_service(
    c: Connection,
    remote_dir: str = "~/kiosk_dashboard",
    service_name: str = "kiosk-dashboard",
) -> None:
    expanded_dir = _expand_remote_dir(c, remote_dir)
    home_dir = _remote_home(c)
    unit = _service_unit(expanded_dir, service_user=c.user, home_dir=home_dir)
    tmp_path = f"/tmp/{service_name}.service"
    c.put(StringIO(unit), tmp_path)
    c.sudo(f"mv {tmp_path} /etc/systemd/system/{service_name}.service")
    c.sudo("systemctl daemon-reload")
    c.sudo(f"systemctl enable --now {service_name}.service")


@task
def restart(c: Connection, service_name: str = "kiosk-dashboard") -> None:
    c.sudo(f"systemctl restart {service_name}.service")


@task
def deploy(
    c: Connection,
    remote_dir: str = "~/kiosk_dashboard",
    service_name: str = "kiosk-dashboard",
) -> None:
    sync(c, remote_dir=remote_dir)
    ensure_uv(c)
    uv_sync(c, remote_dir=remote_dir)
    install_service(c, remote_dir=remote_dir, service_name=service_name)
    restart(c, service_name=service_name)
