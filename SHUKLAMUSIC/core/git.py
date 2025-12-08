import asyncio
import shlex
from typing import Tuple

import config
from ..logging import LOGGER

# -------------------------------------------------------
# SAFE ON HEROKU (NO GIT OPERATIONS)
# -------------------------------------------------------

def install_req(cmd: str) -> Tuple[str, str, int, int]:
    async def run_cmd():
        args = shlex.split(cmd)
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        return (
            stdout.decode("utf-8", "replace").strip(),
            stderr.decode("utf-8", "replace").strip(),
            process.returncode,
            process.pid,
        )

    return asyncio.get_event_loop().run_until_complete(run_cmd())


def git():
    """
    Disabled auto-update for Heroku.
    Heroku does not allow `.git` folder or Git operations.
    """
    LOGGER(__name__).info("Skipping Git auto-update (Heroku-safe mode).")

    # Still install requirements if needed
    try:
        LOGGER(__name__).info("Installing requirements...")
        install_req("pip3 install --no-cache-dir -r requirements.txt")
    except Exception as e:
        LOGGER(__name__).error(f"Failed to install requirements: {e}")

    LOGGER(__name__).info("Git function finished (Heroku compatible).")
