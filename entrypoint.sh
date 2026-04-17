#!/bin/sh
# Runs scheduler + telegram listener side-by-side. If either dies, the
# container exits so Railway restarts the whole thing cleanly.

set -e

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
