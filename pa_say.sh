#!/bin/sh

message="$@"

SOCKET=$(dirname $0)/incoming
exec cat >"$SOCKET" <<EOF
{"intent": "$message", "from": {"media": "incoming", "device": "$(hostname)"}}
EOF
