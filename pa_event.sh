#!/bin/sh

message="$@"

SOCKET=$(dirname $0)/incoming
exec cat >"$SOCKET" <<EOF
{"event": "$message", "from": {"media": "incoming", "device": "$(hostname)"}}
EOF
