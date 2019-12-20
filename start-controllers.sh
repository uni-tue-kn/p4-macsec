#!/bin/bash

if [[ $EUID -ne 0 ]]; then
   echo "This script needs to be run as root" 
   exit 1
fi

# configure tmux windows
tmux new -s controllers -d
tmux set -g mouse on
tmux split-window -h
tmux split-window -v -t 0
tmux split-window -v -t 1

# Pane numbers
# 0 2
# 1 3

# start controllers
tmux send-keys -t 0 'printf "\033]2;%s\033\\" "Global Controller"' Enter C-l
tmux send-keys -t 0 'cd controller' Enter
tmux send-keys -t 0 './controller.py' Enter
tmux send-keys -t 1 'printf "\033]2;%s\033\\" "Controller s1"' Enter C-l
tmux send-keys -t 1 'cd controller_distributed' Enter
tmux send-keys -t 1 './controller.py -a 127.0.0.1:50051 -n s1 -s ipc:///tmp/bmv2-0-notifications.ipc -m 00:00:00:FF:01:01' Enter
tmux send-keys -t 2 'printf "\033]2;%s\033\\" "Controller s2"' Enter C-l
tmux send-keys -t 2 'cd controller_distributed' Enter
tmux send-keys -t 2 './controller.py -a 127.0.0.1:50052 -n s2 -s ipc:///tmp/bmv2-1-notifications.ipc -d 1 -l localhost:52002 -m 00:00:00:FF:02:02' Enter
tmux send-keys -t 3 'printf "\033]2;%s\033\\" "Controller s3"' Enter C-l
tmux send-keys -t 3 'cd controller_distributed' Enter
tmux send-keys -t 3 './controller.py -a 127.0.0.1:50053 -n s3 -s ipc:///tmp/bmv2-2-notifications.ipc -d 2 -l localhost:52003 -m 00:00:00:FF:03:03' Enter

tmux attach -t controllers
