#!/bin/bash

SESSION=assistant

if ! (pgrep tmux && tmux has-session -t $SESSION) ; then
    tmux new -d -s $SESSION
    while ! (pgrep tmux && tmux has-session -t $SESSION); do
	sleep 1
    done
fi

send_line() {
    tmux send-keys -t $SESSION "$1"
    tmux send-keys -t $SESSION Enter
}

send_line "cd ~/Projects/pa; ./main.py"
