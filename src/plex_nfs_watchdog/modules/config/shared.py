import sys
from argparse import Namespace
from pathlib import Path

system_paths: dict[str, str] = {
    'win32': f"AppData/Roaming",
    'linux': f".local/share",
    'darwin': f"Library/Application Support",
}
cache_path: Path = Path(f"{str(Path.home())}/{system_paths[sys.platform]}/plex_nfs_watchdog_cache/plex_config.json")

VERSION: str = "0.0.3"
user_input: Namespace
