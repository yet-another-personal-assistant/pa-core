#!/bin/bash

THISDIR=$(dirname $0)

SESSION=assistant

if ! (pgrep tmux && tmux has-session -t $SESSION) ; then
    tmux new -d -s $SESSION
    while ! (pgrep tmux && tmux has-session -t $SESSION); do
	sleep 1
    done
fi

send_line() {
    for arg in $@ ; do
        tmux send-keys -t $SESSION "'"$arg"'"
        tmux send-keys -t $SESSION Space
    done
    tmux send-keys -t $SESSION Enter
}

(cd $THISDIR && ./link_dbus.sh)

send_line cd $THISDIR
send_line .env/bin/python3 ./main.py $@
