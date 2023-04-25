from watchdog.events import FileSystemEventHandler

from ..plex.plex_agent import plex_agent_singleton


class PlexWatchdog(FileSystemEventHandler):

    def on_any_event(self, event):
        plex_agent_singleton.parse_event(event)
