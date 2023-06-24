import sys
from glob import glob
from os import environ
from pathlib import Path
from shutil import copy
from typing import Literal

from dotenv import set_key
from invoke.context import Context
from invoke.runners import Result
from invoke.tasks import task

Environments = Literal["dev", "prod"]

stack_name_dev = "adit_dev"
stack_name_prod = "adit_prod"

project_dir = Path(__file__).resolve().parent
compose_dir = project_dir / "compose"

compose_file_base = compose_dir / "docker-compose.base.yml"
compose_file_dev = compose_dir / "docker-compose.dev.yml"
compose_file_prod = compose_dir / "docker-compose.prod.yml"

###
# Helper functions
###


def get_stack_name(env: Environments):
    if env == "dev":
        return stack_name_dev
    elif env == "prod":
        return stack_name_prod
    else:
        raise ValueError(f"Unknown environment: {env}")


def build_compose_cmd(env: Environments):
    base_compose_cmd = f"docker compose -f '{compose_file_base}'"
    stack_name = get_stack_name(env)
    if env == "dev":
        return f"{base_compose_cmd} -f '{compose_file_dev}' -p {stack_name}"
    elif env == "prod":
        return f"{base_compose_cmd} -f '{compose_file_prod}' -p {stack_name}"
    else:
        raise ValueError(f"Unknown environment: {env}")


def check_compose_up(ctx: Context, env: Environments):
    stack_name = get_stack_name(env)
    result = ctx.run("docker compose ls", hide=True, warn=True)
    assert result and result.ok
    for line in result.stdout.splitlines():
        if line.startswith(stack_name) and line.find("running") != -1:
            return True
    return False


def run_cmd(ctx: Context, cmd: str, silent=False) -> Result:
    if not silent:
        print(f"Running: {cmd}")

    hide = True if silent else None

    result = ctx.run(cmd, pty=True, hide=hide)
    assert result and result.ok
    return result


###
# Tasks
###


@task
def compose_build(ctx: Context, env: Environments = "dev"):
    """Build ADIT image for specified environment"""
    cmd = f"{build_compose_cmd(env)} build"
    run_cmd(ctx, cmd)


@task
def compose_up(ctx: Context, env: Environments = "dev", no_build: bool = False):
    """Start ADIT containers in specified environment"""
    build_opt = "--no-build" if no_build else "--build"
    cmd = f"{build_compose_cmd(env)} up {build_opt} --detach"
    run_cmd(ctx, cmd)


@task
def compose_down(ctx: Context, env: Environments = "dev", cleanup: bool = False):
    """Stop ADIT containers in specified environment"""
    cmd = f"{build_compose_cmd(env)} down"
    if cleanup:
        cmd += " --remove-orphans --volumes"
    run_cmd(ctx, cmd)


@task
def compose_restart(ctx: Context, env: Environments = "dev", service: str | None = None):
    """Restart ADIT containers in specified environment"""
    cmd = f"{build_compose_cmd(env)} restart"
    if service:
        cmd += f" {service}"
    run_cmd(ctx, cmd)


@task
def compose_logs(
    ctx: Context, env: Environments = "dev", service: str | None = None, follow: bool = False
):
    """Show logs of ADIT containers in specified environment"""
    cmd = f"{build_compose_cmd(env)} logs"
    if service:
        cmd += f" {service}"
    if follow:
        cmd += " --follow --tail 1000"
    run_cmd(ctx, cmd)


@task
def stack_deploy(ctx: Context, env: Environments = "prod"):
    """Deploy the stack to Docker Swarm (prod by default!)."""
    stack_name = get_stack_name(env)
    suffix = f"-c {compose_file_base}"
    if env == "dev":
        suffix += f" -c {compose_file_dev} {stack_name}"
    elif env == "prod":
        suffix += f" -c {compose_file_prod} {stack_name}"
    else:
        raise ValueError(f"Unknown environment: {env}")

    cmd = f"docker stack deploy {suffix}"
    run_cmd(ctx, cmd)


@task
def stack_rm(ctx: Context, env: Environments = "prod"):
    """Remove the stack from Docker Swarm (prod by default!)."""
    stack_name = get_stack_name(env)
    cmd = f"docker stack rm {stack_name}"
    run_cmd(ctx, cmd)


@task
def format(ctx: Context):
    """Format the source code (black, ruff, djlint)"""
    # Format Python code
    black_cmd = "poetry run black ./adit"
    run_cmd(ctx, black_cmd)
    # Sort Python imports
    ruff_cmd = "poetry run ruff . --fix --select I"
    run_cmd(ctx, ruff_cmd)
    # Format Django templates
    djlint_cmd = "poetry run djlint . --reformat"
    run_cmd(ctx, djlint_cmd)


@task
def lint(ctx: Context):
    """Lint the source code (ruff, djlint, pyright)"""
    cmd_ruff = "poetry run ruff ."
    run_cmd(ctx, cmd_ruff)
    cmd_djlint = "poetry run djlint . --lint"
    run_cmd(ctx, cmd_djlint)
    cmd_pyright = "poetry run pyright"
    run_cmd(ctx, cmd_pyright)


@task
def test(
    ctx: Context,
    path: str = "./adit",
    cov: bool = False,
    keyword: str | None = None,
    mark: str | None = None,
    stdout: bool = False,
):
    """Run the test suite"""
    if not check_compose_up(ctx, "dev"):
        sys.exit(
            "Integration tests need ADIT dev containers running.\nRun 'invoke compose-up' first."
        )

    cmd = (
        f"{build_compose_cmd('dev')} exec "
        "--env DJANGO_SETTINGS_MODULE=adit.settings.test web pytest "
    )
    if cov:
        cmd += "--cov=adit "
    if keyword:
        cmd += f"-k {keyword} "
    if mark:
        cmd += f"-m {mark} "
    if stdout:
        cmd += "-s "

    cmd += path
    run_cmd(ctx, cmd)


@task
def ci(ctx: Context):
    """Run the continuous integration (linting and tests)"""
    lint(ctx)
    test(ctx, cov=True)


@task
def reset_adit_dev(ctx: Context):
    """Reset ADIT dev container environment"""
    # Reset Orthancs
    reset_orthancs_cmd = f"{build_compose_cmd('dev')} exec web python manage.py reset_orthancs"
    run_cmd(ctx, reset_orthancs_cmd)
    # Wipe the database
    flush_cmd = f"{build_compose_cmd('dev')} exec web python manage.py flush --noinput"
    run_cmd(ctx, flush_cmd)
    # Populate the database with example data
    populate_dev_db_cmd = f"{build_compose_cmd('dev')} exec web python manage.py populate_dev_db"
    run_cmd(ctx, populate_dev_db_cmd)


@task
def adit_web_shell(ctx: Context, env: Environments = "dev"):
    """Open Python shell in ADIT web container of specified environment"""
    cmd = f"{build_compose_cmd(env)} exec web python manage.py shell_plus"
    run_cmd(ctx, cmd)


@task
def copy_statics(ctx: Context):
    """Copy JS and CSS dependencies from node_modules to static vendor folder"""
    print("Copying statics...")

    copy("node_modules/jquery/dist/jquery.js", "adit/static/vendor/")
    for file in glob("node_modules/bootstrap/dist/css/bootstrap.css*"):
        copy(file, "adit/static/vendor/")
    for file in glob("node_modules/bootstrap/dist/js/bootstrap.bundle.js*"):
        copy(file, "adit/static/vendor/")
    copy("node_modules/bootswatch/dist/flatly/bootstrap.css", "adit/static/vendor/")
    for file in glob("node_modules/alpinejs/dist/alpine*.js"):
        copy(file, "adit/static/vendor/")
    copy("node_modules/morphdom/dist/morphdom-umd.js", "adit/static/vendor/")
    copy("node_modules/htmx.org/dist/htmx.js", "adit/static/vendor/")
    copy("node_modules/htmx.org/dist/ext/ws.js", "adit/static/vendor/htmx-ws.js")
    copy(
        "node_modules/htmx.org/dist/ext/morphdom-swap.js",
        "adit/static/vendor/htmx-morphdom-swap.js",
    )


@task
def init_workspace(ctx: Context, type: Literal["codespaces", "gitpod"]):
    """Initialize workspace for Github Codespaces or Gitpod"""
    env_dev_file = f"{compose_dir}/.env.dev"
    copy(f"{project_dir}/example.env", env_dev_file)

    if type == "codespaces":
        base_url = f"https://{environ['CODESPACE_NAME']}-8000.preview.app.github.dev"
    elif type == "gitpod":
        result = run_cmd(ctx, "gp url 8000", silent=True)
        assert result and result.ok
        base_url = result.stdout.strip()
    else:
        raise ValueError(f"Invalid workspace type: {type}")

    host = base_url.removeprefix("https://")
    host += ",localhost"

    set_key(env_dev_file, "BASE_URL", base_url, quote_mode="never")
    set_key(env_dev_file, "DJANGO_CSRF_TRUSTED_ORIGINS", base_url, quote_mode="never")
    set_key(env_dev_file, "DJANGO_ALLOWED_HOSTS", host, quote_mode="never")
    set_key(env_dev_file, "DJANGO_INTERNAL_IPS", host, quote_mode="never")
    set_key(env_dev_file, "FORCE_DEBUG_TOOLBAR", "true", quote_mode="never")


@task
def show_outdated(ctx: Context):
    """Show outdated dependencies"""
    print("### Outdated Python dependencies ###")
    poetry_cmd = "poetry show --outdated --top-level"
    result = run_cmd(ctx, poetry_cmd)
    print(result.stderr.strip())

    print("### Outdated NPM dependencies ###")
    npm_cmd = "npm outdated"
    run_cmd(ctx, npm_cmd)


@task
def upgrade(ctx: Context):
    """Upgrade Python and JS packages"""
    run_cmd(ctx, "poetry update")
    run_cmd(ctx, "npm update")
    copy_statics(ctx)


@task
def try_github_actions(ctx: Context):
    """Try Github Actions locally using Act"""
    act_path = project_dir / "bin" / "act"
    if not act_path.exists():
        print("Installing act...")
        run_cmd(
            ctx,
            "curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash",
            silent=True,
        )

    run_cmd(ctx, f"{act_path} -P ubuntu-latest=catthehacker/ubuntu:act-latest")
