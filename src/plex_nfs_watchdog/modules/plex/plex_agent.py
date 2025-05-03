import json
import logging
import pprint
from pathlib import Path
from threading import Event, Thread
from typing import Optional

from plexapi.server import PlexServer

from ..config import shared


class PlexAgent:
    _plex_config: dict[str, str] = {}
    _server: PlexServer = None
    _internal_sections: dict = {}
    _fast_section_lookup: set[str] = set()
    _scan_queue: list[tuple[str, str]] = list()
    _supported_ext: list[str] = [
        "3g2",
        "3gp",
        "amv",
        "asf",
        "ass",
        "avi",
        "drc",
        "f4a",
        "f4b",
        "f4p",
        "f4v",
        "flac",
        "flv",
        "gif",
        "gifv",
        "idx",
        "m2ts",
        "m2v",
        "m4p",
        "m4v",
        "m4v",
        "mkv",
        "mng",
        "mov",
        "mp2",
        "mp3",
        "mp4",
        "mpe",
        "mpeg",
        "mpg",
        "mpv",
        "mxf",
        "nsv",
        "ogg",
        "ogv",
        "qt",
        "rm",
        "rmvb",
        "roq",
        "smi",
        "srt",
        "ssa",
        "sub",
        "svi",
        "ts",
        "vob",
        "vtt",
        "wmv",
        "yuv",
        "webm",
    ]

    def _is_refreshing(self) -> bool:
        """
        Check if any section of the Plex server is refreshing
        :return: True if any section is refreshing, False otherwise
        """
        for section in self._server.library.sections():
            if shared.user_input.verbose:
                logging.info(f"Checking refreshing status for section {section.title}")
            if section.refreshing:
                return True
        return False

    def _get_id_from_root_folder(self, root_folder: str) -> str:
        """
        Retrieves the ID of a section from one root folder name
        :param root_folder: A root folder name
        :return: The ID of the section, raises ValueError if not found
        """
        for id, section_data in self._internal_sections.items():
            if root_folder in section_data["root_folders"]:
                return id
        raise ValueError(f"Root folder {root_folder} not found in Plex sections")

    def tokenized(self) -> bool:
        """
        Check if the config contains a token
        :return: True if the config contains a token, False otherwise
        """
        return self._plex_config["token"] is not None

    def load_config_cache(self) -> None:
        """
        If the cache file exists, it loads the Plex credentials from the cache
        """
        try:
            if shared.cache_path.exists():
                logging.info(f"Found Plex configuration from cache: {shared.cache_path}")
                with open(shared.cache_path, "r") as cache_file:
                    self._plex_config = json.load(cache_file)
        except OSError as e:
            logging.error(f"Could not load Plex configuration from cache: {e}")
            exit(-1)

    def _save_config_cache(self) -> None:
        """
        Saves the Plex Credentials to a cache file for later use
        """
        try:
            logging.info(f"Saving Plex configuration to cache: {shared.cache_path}")
            if not shared.cache_path.parent.exists():
                shared.cache_path.parent.mkdir(parents=True)
            with open(shared.cache_path, "w") as cache_file:
                json.dump(self._plex_config, cache_file)
        except OSError as e:
            logging.error(f"Could not save Plex configuration to cache: {e}")
            exit(-1)

    def _eval_config(self) -> None:
        """
        Evaluates the Plex configuration and checks if it needs to be updated
        """
        save_file: bool = False
        if not self._plex_config:
            self._plex_config["host"] = shared.user_input.host
            self._plex_config["token"] = shared.user_input.token
            save_file = True
        else:
            if (
                shared.user_input.token is not None and shared.user_input.token != self._plex_config["token"]
            ) or self._plex_config["host"] != shared.user_input.host:
                logging.warning("Plex credentials are different from the cached one!")
                while True:
                    answer: str = (
                        "y"
                        if shared.user_input.always_overwrite_config
                        else input("Do you want to overwrite the cached configuration? [y/N]: ").lower()
                    )
                    if answer == "y":
                        logging.info("Overwriting cached configuration...")
                        self._plex_config["host"] = shared.user_input.host
                        if shared.user_input.token is not None:
                            self._plex_config["token"] = shared.user_input.token
                        save_file = True
                        break
                    elif answer == "n":
                        break
        if save_file:
            self._save_config_cache()

    def connect(self) -> None:
        """
        Connects to the Plex server and loads the internal paths
        """
        self._eval_config()
        try:
            self._server = PlexServer(baseurl=self._plex_config["host"], token=self._plex_config["token"], timeout=60)
            logging.info(f"Connected to Plex server ({self._server.version})")
            if self._inspect_library() == 0:
                logging.error("No Plex sections detected, please check your configuration")
                exit(-1)
            logging.info(f"Found sections:\n{pprint.pformat(self._internal_sections)}")
        except Exception as e:
            logging.error(f"Unable to connect to Plex server:\n{e}")
            exit(-1)

    def _inspect_library(self) -> int:
        """
        Inspects the Plex library and loads the internal paths.
        For each section, it stores the ID, title, locations and unique root folders
        :return: The number of sections found
        """
        for section in self._server.library.sections():
            self._internal_sections[section.key] = {"title": section.title, "locations": [], "root_folders": set()}
            for location in section.locations:
                tmp = Path(location)
                if tmp not in self._internal_sections[section.key]["locations"]:
                    self._internal_sections[section.key]["locations"].append(tmp)
                self._internal_sections[section.key]["root_folders"].add(tmp.name)
                self._fast_section_lookup.add(tmp.name)
        return len(self._internal_sections)

    def is_plex_section(self, folder_name: str) -> bool:
        """
        Checks if the given path is a Plex section
        :param folder_name: The folder name to check
        :return bool: True if the given folder_name is a Plex section, False otherwise
        """
        return folder_name in self._fast_section_lookup

    def validate_path(self, path: Path) -> Optional[tuple[str, str]]:
        """
        Validates the given path by applying the following rules:
        1. If the path is a file and the extension is not in the supported list, return None
        2. If the path is a directory, check if it is child of a Plex section
        :param path: The path to validate
        :return: A tuple containing the section ID and the item name if valid, None otherwise
        """
        if shared.user_input.verbose:
            logging.info(f"Analyzing {path.absolute()}")
        if path.is_file() and path.suffix[1:] not in self._supported_ext:
            if shared.user_input.verbose:
                logging.info(f"File {path.name} is not a supported file type")
            return None
        cursor = path
        while len(cursor.parents) != 0:
            if cursor.parent.name in self._fast_section_lookup:
                id = self._get_id_from_root_folder(cursor.parent.name)
                return id, cursor.name
            else:
                cursor = cursor.parent
        if shared.user_input.verbose:
            logging.info(f"Path {path.absolute()} is not a child of a Plex section")
        return None

    def _scan(self, section_id: str, item: str) -> None:
        """
        Request Plex to scan the given item in the given section
        :param section_id: The id of the section to scan
        :param item: The folder name to scan
        """
        plex_section = self._server.library.sectionByID(section_id)
        for location in self._internal_sections[section_id]["locations"]:
            scan_path: Path = Path(location / item).absolute()
            if not self._server.isBrowsable(scan_path):
                logging.info(f"Skipping Plex scan for {str(scan_path)} because it is not browsable")
                continue
            logging.info(f"Requesting Plex to scan the remote path {str(scan_path)}")
            if shared.user_input.dry_run:
                logging.info("Skipping Plex scan due to dry-run")
            else:
                plex_section.update(str(scan_path))

    def manual_scan(self, paths: set[Path]) -> None:
        """
        Scans the given paths manually
        :param paths: A list of paths to scan
        """
        for user_paths in paths:
            validation = self.validate_path(user_paths)
            if validation is None:
                logging.warning(f"Path {user_paths.absolute()} is not a valid path to scan")
                continue
            self._scan(validation[0], validation[1])

    def parse_event(self, event) -> None:
        """
        Parses the event generated by the daemon watcher and adds it to the scan queue
        :param event:
        :return:
        """
        event_type: str = event.event_type
        event_path: Path = Path(event.src_path) if event_type != "moved" else Path(event.dest_path)
        if event.is_directory:
            if not shared.user_input.allow_folder:
                if shared.user_input.verbose:
                    logging.info(f"Skipping directory event: {event_path}")
                return
        validation = self.validate_path(event_path)
        if validation is None:
            return
        if validation not in self._scan_queue:
            logging.info(
                f"Adding to queue for section {self._internal_sections[validation[0]]['title']} ({event_type}): {validation[1]}"
            )
            self._scan_queue.append(validation)

    def start_service(self) -> ():
        """
        Start the Plex NFS Watchdog daemon thread. Every interval, if there is no Plex refresh, it will scan the queue
        :return: A callback to stop the thread
        """
        stopped = Event()

        def loop():
            while not stopped.wait(shared.user_input.interval):
                if self._scan_queue:
                    if self._is_refreshing():
                        logging.info("Plex server is refreshing, skipping scan")
                        continue
                    section, item = self._scan_queue.pop(0)
                    self._scan(section, item)

        Thread(target=loop).start()
        return stopped.set


plex_agent_singleton = PlexAgent()
