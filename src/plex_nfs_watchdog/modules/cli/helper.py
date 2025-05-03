import argparse
from pathlib import Path

from ..config import shared
from ..plex.plex_agent import plex_agent_singleton


def get_args_from_cli() -> None:
    """
    Parses the command line arguments and stores them in the shared config
    """
    parser = argparse.ArgumentParser(
        prog="PlexNFSWatchdog",
        description="A utility to trigger Plex partial-scans on NFS configurations, on which inotify is not supported.",
    )
    action_type = parser.add_mutually_exclusive_group(required=True)
    action_type.add_argument(
        "--scan", "-s", action="store_true", help="Manually triggers a partial-scan on the given folder paths."
    )
    action_type.add_argument(
        "--daemon",
        "-d",
        action="store_true",
        help="Starts a watchdog daemon to automatically triggers a partial-scan on the given folder paths.",
    )
    parser.add_argument("--paths", "-p", action="store", nargs="+", required=True, help="A list of folder paths.", type=Path)
    parser.add_argument(
        "--host",
        "-H",
        action="store",
        help="The host of the Plex server.",
        type=str,
        default="http://localhost:32400",
        required=False,
    )
    parser.add_argument(
        "--token", "-t", action="store", help="The token of the Plex server.", type=str, default=None, required=False
    )
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode, does not  send any request of partial-scans.")
    parser.add_argument(
        "--interval",
        "-i",
        help="The interval in seconds to wait between partial-scans when using --daemon. Default is 60 seconds.",
        action="store",
        type=int,
        required=False,
        default=60,
    )
    parser.add_argument(
        "--version",
        "-v",
        help="Prints the version of the application.",
        action="version",
        version=f"%(prog)s {shared.VERSION}",
    )
    parser.add_argument(
        "--listeners",
        "-l",
        action="store",
        nargs="+",
        required=False,
        help="List of events to watch when using --daemon.",
        type=str,
        choices=shared.listeners_type,
        default=None,
    )
    parser.add_argument("--allow-folder", action="store_true", help="Enable daemon mode folder trigger.")
    parser.add_argument(
        "--always-overwrite-config",
        action="store_true",
        help="Set this to always overwrite the config file when the credentials do not match with cache.",
    )
    shared.user_input = parser.parse_args()
    shared.user_input.paths = set(shared.user_input.paths)
    if shared.user_input.daemon:
        if shared.user_input.interval <= 0:
            parser.error("--interval is required when using --daemon. It must be a not zero positive integer")
        if shared.user_input.listeners is None:
            parser.error("--listeners is required when using --daemon. It must be one or more valid event type")
    if shared.user_input.token is None and not plex_agent_singleton.tokenized():
        parser.error("Plex token is required. Use --token to provide it.")
