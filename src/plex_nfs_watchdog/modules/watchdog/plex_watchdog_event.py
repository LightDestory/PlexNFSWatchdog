from watchdog.events import FileSystemEventHandler

from ..config import shared
from ..plex.plex_agent import plex_agent_singleton


class PlexWatchdog(FileSystemEventHandler):
    """
    PlexWatchdog is a class that handles file system events for Plex NFS Watchdog.
    It inherits from FileSystemEventHandler and overrides methods to send events to the Plex agent.
    """

    def on_moved(self, event):
        if "move" in shared.user_input.listeners:
            plex_agent_singleton.parse_event(event)

    def on_modified(self, event):
        if "modify" in shared.user_input.listeners:
            plex_agent_singleton.parse_event(event)

    def on_created(self, event):
        if "create" in shared.user_input.listeners:
            plex_agent_singleton.parse_event(event)

    def on_deleted(self, event):
        if "delete" in shared.user_input.listeners:
            plex_agent_singleton.parse_event(event)

    def on_closed(self, event):
        if "io_close" in shared.user_input.listeners:
            plex_agent_singleton.parse_event(event)

    def on_opened(self, event):
        if "io_open" in shared.user_input.listeners:
            plex_agent_singleton.parse_event(event)
