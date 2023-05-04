import json
import logging
import pprint

from plexapi.server import PlexServer
from pathlib import Path
from threading import Event, Thread

from ..config import shared


class PlexAgent:
    __plex_config: dict[str, str] = {}
    __server: PlexServer = None
    __save_cache: bool = False
    __internal_paths: dict[str, tuple[str, str]] = {}
    __notify_queue: list[tuple[str, str]] = list()
    __supported_ext: list[str] = [
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
        "webm"
    ]

    def is_cache_loaded(self) -> bool:
        """
        Checks if the Plex configuration is set
        :return bool: True if the Plex configuration is set, False otherwise
        """
        return self.__plex_config != {}

    def load_config_cache(self) -> None:
        """
        Loads the Plex configuration from the cache
        :return:
        """
        try:
            logging.info(f"Found Plex configuration from cache: {shared.cache_path}")
            with open(shared.cache_path, "r") as cache_file:
                self.__plex_config = json.load(cache_file)
        except OSError as e:
            logging.error(f"Could not load Plex configuration from cache: {e}")
            exit(-1)

    def __save_config_cache(self) -> None:
        """
        Saves the Plex configuration to the cache
        :return:
        """
        try:
            logging.info(f"Saving Plex configuration to cache: {shared.cache_path}")
            if not shared.cache_path.parent.exists():
                shared.cache_path.parent.mkdir(parents=True)
            with open(shared.cache_path, "w") as cache_file:
                json.dump(self.__plex_config, cache_file)
        except OSError as e:
            logging.error(f"Could not save Plex configuration to cache: {e}")
            exit(-1)

    def __eval_config(self) -> None:
        """
        Returns the Plex configuration, it is ensured that host and token are available from cli or cache
        :return:
        """
        if shared.user_input.token and not self.__plex_config:
            self.__plex_config['host'] = shared.user_input.host
            self.__plex_config['token'] = shared.user_input.token
            self.__save_cache = True
        elif shared.user_input.token and self.__plex_config:
            if self.__plex_config['host'] != shared.user_input.host \
                    or self.__plex_config['token'] != shared.user_input.token:
                logging.warning("Plex host and/or token are different from the cached ones!")
                while True:
                    answer: str = input("Do you want to overwrite the cached configuration? [y/N]: ").lower()
                    if answer == 'y':
                        self.__plex_config['host'] = shared.user_input.host
                        self.__plex_config['token'] = shared.user_input.token
                        self.__save_cache = True
                        break
                    elif answer == 'n':
                        break

    def connect(self) -> None:
        """
        Connects to the Plex server
        :return:
        """
        self.__eval_config()
        try:
            self.__server = PlexServer(self.__plex_config["host"], self.__plex_config["token"])
            logging.info("Connected to Plex server")
            logging.debug(f"Plex version: {self.__server.version}")
            self.__inspect_library()
            num_detected_sections: int = len(self.__internal_paths)
            if num_detected_sections == 0:
                logging.error("No Plex sections detected, please check your configuration")
                exit(-1)
            logging.debug(f"Found {num_detected_sections} Plex sections:\n{pprint.pformat(self.__internal_paths)}")
            if self.__save_cache:
                self.__save_config_cache()
        except Exception as e:
            logging.error(f"Unable to connect to Plex server:\n{e}")
            exit(-1)

    def __inspect_library(self) -> None:
        """
        Loads the internal paths from the Plex server
        :return:
        """
        for section in self.__server.library.sections():
            remote_path: str = section.locations[0]
            self.__internal_paths[Path(remote_path).name] = (section.title, remote_path)

    def is_plex_section(self, folder_name: str) -> bool:
        """
        Checks if the given path is a Plex section
        :param folder_name: The folder name to check
        :return bool: True if the given folder_name is a Plex section, False otherwise
        """
        return folder_name in self.__internal_paths.keys()

    def __find_section_child_of(self, item: Path) -> Path | None:
        """
        Finds the direct child of the Plex section of the given item
        :param item: The item to find the section of
        :return: The direct child of the Plex section of the given item
        """
        while item.parent.name not in self.__internal_paths.keys():
            if len(item.parents) == 0:
                return None
            item = item.parent
        return item

    def _scan(self, section: str, item: str) -> None:
        """
        Scans the given item in the given section
        :param section: The section to scan
        :param item: The item to scan
        :return:
        """
        section_title, section_path = self.__internal_paths[section]
        plex_section = self.__server.library.section(section_title)
        if plex_section.refreshing:
            if shared.user_input.daemon:
                logging.warning(f"Plex section {section_title} is already refreshing, re-scheduling...")
                self.__notify_queue.append((section, item))
            else:
                logging.warning(f"Plex section {section_title} is already refreshing, skipping...")
            return
        scan_path: Path = Path(f"{section_path}/{item}")
        logging.info(f"Requesting Plex to scan remote path {str(scan_path)}")
        if shared.user_input.dry_run:
            logging.info(f"Skipping Plex scan due to dry-run")
        else:
            plex_section.update(str(scan_path))

    def manual_scan(self, paths: set[Path]) -> None:
        """
        Manually scans the given paths
        :param paths: A list of paths to scan
        :return:
        """
        scan_sections: set[tuple[str, str]] = set()
        for given_path in paths:
            logging.info(f"Analyzing {given_path}")
            section_child: Path | None = self.__find_section_child_of(given_path)
            if section_child is None:
                logging.error(f"Could not find Plex section for {given_path}")
                continue
            else:
                scan_sections.add((section_child.parent.name, section_child.name))
        for (section, item) in scan_sections:
            self._scan(section, item)

    def parse_event(self, event) -> None:
        """
        Parses the given event and adds it to the queue
        :param event: The event to parse
        :return:
        """
        event_type: str = event.event_type
        event_path: Path = Path(event.src_path) if event_type != 'moved' else Path(event.dest_path)
        if event_path.name in self.__internal_paths.keys():
            return
        section_child: Path | None = self.__find_section_child_of(event_path)
        if section_child is None:
            logging.error(f"Could not find Plex section for {event_path}")
            return
        section_scan = (section_child.parent.name, section_child.name)
        if section_scan not in self.__notify_queue:
            logging.info(f"Adding to queue ({event_type}): {section_child.name}")
            self.__notify_queue.append(section_scan)

    def start_service(self) -> ():
        """
        Start a thread to manage a queue of pending scans
        :return callable: A function to stop the thread
        """
        stopped = Event()

        def loop():
            while not stopped.wait(shared.user_input.interval):
                if self.__notify_queue:
                    section, item = self.__notify_queue.pop(0)
                    self._scan(section, item)

        Thread(target=loop).start()
        return stopped.set


plex_agent_singleton = PlexAgent()
