#!/bin/sh

CMD="python plex_nfs_watchdog.py --daemon"

[ -n "$WATCH_PATHS" ] && CMD="$CMD --paths $WATCH_PATHS"
[ -n "$PLEX_SERVER" ] && CMD="$CMD --host $PLEX_SERVER"
[ -n "$PLEX_TOKEN" ] && CMD="$CMD --token $PLEX_TOKEN"
[ -n "$SCAN_INTERVAL" ] && CMD="$CMD --interval $SCAN_INTERVAL"
[ -n "$LISTENERS" ] && CMD="$CMD --listeners $LISTENERS"

echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Starting up watchdog: $CMD"

exec $CMD 2>&1
