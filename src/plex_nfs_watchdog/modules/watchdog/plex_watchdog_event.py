from watchdog.events import FileSystemEventHandler

from ..plex.plex_agent import plex_agent_singleton


class PlexWatchdog(FileSystemEventHandler):

    def on_any_event(self, event):
        if not event.is_directory:
            return
        plex_agent_singleton.parse_event(event)
