import logging
import os
import sys
import time

import colorlog
from watchdog.observers import Observer

sys.path.append(os.path.join(os.path.dirname(__file__), "."))
from modules.cli.helper import get_args_from_cli
from modules.config import shared
from modules.plex.plex_agent import plex_agent_singleton
from modules.watchdog.plex_watchdog_event import PlexWatchdog

colorlog.basicConfig(
    format="{log_color}{levelname}:\t{message}",
    level=logging.INFO,
    style="{",
    stream=None,
    log_colors={"DEBUG": "cyan", "INFO": "white", "WARNING": "yellow", "ERROR": "red", "CRITICAL": "red"},
)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("watchdog").setLevel(logging.WARNING)


def daemon_mode() -> None:
    """
    Daemon mode for Plex NFS Watchdog.
    This function sets up the PlexWatchdog event handler and starts the observer to monitor file system events.
    It checks the provided paths to ensure they are valid Plex sections and schedules them for monitoring.
    """
    event_handler: PlexWatchdog = PlexWatchdog()
    observer: Observer = Observer()
    valid_paths: int = 0
    for path in shared.user_input.paths:
        full_path = path.resolve()
        if not path.exists() or not path.is_dir() or not plex_agent_singleton.is_plex_section(path.name):
            logging.warning(f"Skipping {full_path} because do not exist or not a directory or not a Plex section")
            continue
        logging.info(f"Scheduling watcher for {full_path}")
        observer.schedule(event_handler, full_path, recursive=True)
        valid_paths += 1
    if valid_paths == 0:
        logging.error("No valid paths given, exiting...")
        exit(-1)
    stop_plex_watchdog_service: () = None
    try:
        logging.info("Registering inotify watcher...")
        observer.start()
        stop_plex_watchdog_service: () = plex_agent_singleton.start_service()
        logging.info("Ready to operate...")
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        logging.warning("Detected SIGNTERM, stopping PlexNFSWatchdog...")
        observer.stop()
        observer.join()
        if stop_plex_watchdog_service is not None:
            stop_plex_watchdog_service()
    except OSError as os_err:
        logging.error(f"OS error: {os_err}")


def main() -> None:
    """
    Main function to start the Plex NFS Watchdog.
    """
    logging.info(f"Starting Plex NFS Watchdog v{shared.VERSION}...")
    plex_agent_singleton.load_config_cache()
    get_args_from_cli()
    plex_agent_singleton.connect()
    if shared.user_input.scan:
        plex_agent_singleton.manual_scan(shared.user_input.paths)
    else:
        daemon_mode()


if __name__ == "__main__":
    main()
