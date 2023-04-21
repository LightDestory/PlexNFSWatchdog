from watchdog.events import FileSystemEventHandler

from ..plex.plex_agent import plex_agent_singleton


class PlexWatchdog(FileSystemEventHandler):

    def on_created(self, event):
        plex_agent_singleton.parse_event(event)

    def on_modified(self, event):
        plex_agent_singleton.parse_event(event)
