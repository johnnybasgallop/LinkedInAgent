#!/bin/bash
# Runs scheduler + telegram listener side-by-side. If either dies, the
# container exits so Railway restarts the whole thing cleanly.

set -e

# Ensure persistent subdirs exist inside STATE_DIR (defaults to /app).
STATE_DIR="${STATE_DIR:-/app}"
mkdir -p "$STATE_DIR/session" "$STATE_DIR/data"

# Bootstrap LinkedIn session on first boot: if state.json is missing/empty
# and SESSION_STATE_B64 is set, decode it into the volume. After a successful
# seed, the file lives in the volume and subsequent restarts are no-ops.
SESSION_FILE="$STATE_DIR/session/state.json"
if [ ! -s "$SESSION_FILE" ] && [ -n "$SESSION_STATE_B64" ]; then
    echo "[entrypoint] seeding $SESSION_FILE from SESSION_STATE_B64"
    if printf '%s' "$SESSION_STATE_B64" | base64 -d > "$SESSION_FILE"; then
        echo "[entrypoint] seeded $(wc -c < "$SESSION_FILE") bytes"
    else
        echo "[entrypoint] failed to decode SESSION_STATE_B64" >&2
        rm -f "$SESSION_FILE"
    fi
fi

python -m pipeline.messaging.telegram_listener &
LISTENER_PID=$!

python scheduler.py &
SCHEDULER_PID=$!

trap "kill $LISTENER_PID $SCHEDULER_PID 2>/dev/null || true" EXIT INT TERM

# Exit as soon as any child exits (so Railway restarts us).
wait -n
EXIT_CODE=$?
echo "[entrypoint] a process exited with code $EXIT_CODE — shutting down"
exit $EXIT_CODE
