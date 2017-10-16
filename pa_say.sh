#!/bin/sh

message="$@"

SOCKET=/tmp/pa_incoming
exec cat >"$SOCKET" <<EOF
{"intent": "$message", "from": {"media": "incoming", "device": "stronghold"}}
EOF
