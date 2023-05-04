import argparse
import logging
import time
import colorlog
import sys
import os
from pathlib import Path
from watchdog.observers import Observer

sys.path.append(os.path.join(os.path.dirname(__file__), "."))
from modules.watchdog.plex_watchdog_event import PlexWatchdog
from modules.config import shared
from modules.plex.plex_agent import plex_agent_singleton

colorlog.basicConfig(format='{log_color}{levelname}:\t{message}', level=logging.INFO, style='{', stream=None,
                     log_colors={
                         'DEBUG': 'cyan', 'INFO': 'white', 'WARNING': 'yellow', 'ERROR': 'red', 'CRITICAL': 'red'
                     })
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("watchdog").setLevel(logging.WARNING)


def get_args_from_cli() -> None:
    """
    Parses the command line arguments and stores them in the shared config
    :return:
    """
    parser = argparse.ArgumentParser(
        prog="PlexNFSWatchdog",
        description="A utility to trigger Plex partial-scans on NFS configurations, on which inotify is not supported",
    )
    action_type = parser.add_mutually_exclusive_group(required=True)
    action_type.add_argument("--scan", "-s", action='store_true',
                             help="Manually triggers a partial-scan on the given folder paths")
    action_type.add_argument("--daemon", "-d", action='store_true',
                             help="Starts a watchdog daemon to automatically triggers a partial-scan on the given folder paths")
    parser.add_argument("--paths", "-p", action="store", nargs='+', required=True, help="A list of folder paths",
                        type=Path)
    parser.add_argument("--host", "-H", action="store", help="The host of the Plex server", type=str,
                        default="http://localhost:32400", required=False)
    parser.add_argument("--token", "-t", action="store", help="The token of the Plex server", type=str, default=None,
                        required=False)
    parser.add_argument("--dry-run", action='store_true',
                             help="Dry run mode, does not  send any request of partial-scans")
    parser.add_argument("--interval", "-i", help="The interval in seconds to wait between partial-scans",
                        action="store", type=int, required=False, default=None)
    parser.add_argument("--version", "-v", help="Prints the version of the application", action='version',
                        version=f"%(prog)s {shared.VERSION}")
    parser.add_argument("--listeners", "-l", action="store", nargs='+', required=False, help="List of events to watch",
                        type=str, choices=shared.listeners_type, default=None)
    shared.user_input = parser.parse_args()
    shared.user_input.paths = set(shared.user_input.paths)
    if shared.user_input.daemon and (shared.user_input.interval is None or shared.user_input.interval <= 0):
        parser.error("--interval is required when using --daemon. It must be a not zero positive integer")
    if shared.user_input.daemon and shared.user_input.listeners is None:
        parser.error("--listeners is required when using --daemon. It must be a valid event type")
    for given_path in shared.user_input.paths:
        if not given_path.exists() or not given_path.is_dir():
            parser.error(f"{given_path.resolve()} does not exist or it is not a folder!")
    if shared.user_input.token is None and not plex_agent_singleton.is_cache_loaded():
        parser.error("Plex host and token are missing!")


def main() -> None:
    if shared.cache_path.exists():
        plex_agent_singleton.load_config_cache()
    get_args_from_cli()
    plex_agent_singleton.connect()
    if shared.user_input.scan:
        plex_agent_singleton.manual_scan(shared.user_input.paths)
    else:
        event_handler: PlexWatchdog = PlexWatchdog()
        observer: Observer = Observer()
        observers: list[Observer] = []
        for given_path in shared.user_input.paths:
            full_path: str = given_path.resolve()
            if not plex_agent_singleton.is_plex_section(given_path.name):
                logging.warning(f"{full_path}  is not a plex section folder, skipping...")
                continue
            logging.info(f"Scheduling watcher for {full_path}")
            observer.schedule(event_handler, full_path, recursive=True)
            observers.append(observer)
        if not observers:
            logging.error("No valid paths given, exiting...")
            exit(-1)
        stop_plex_watchdog_service: () = None
        try:
            logging.info(f"Registering inotify watcher...")
            observer.start()
            stop_plex_watchdog_service: () = plex_agent_singleton.start_service()
            logging.info(f"Ready to operate...")
            while True:
                time.sleep(2)
        except KeyboardInterrupt:
            logging.warning("Detected SIGNTERM, stopping PlexNFSWatchdog...")
            for observer in observers:
                observer.unschedule_all()
                observer.stop()
                observer.join()
            if stop_plex_watchdog_service is not None:
                stop_plex_watchdog_service()
        except OSError as os_err:
            logging.error(f"OS error: {os_err}")


if __name__ == '__main__':
    main()
