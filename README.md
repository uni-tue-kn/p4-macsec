# P4-MACsec

This projects implements MACsec in BMv2 together with an automated, controller based set-up of MACsec connections. The automated set-up uses a topology discovery using an enhanced version of LLDP that encrypts LLDP payloads. For details, please see the corresponding [paper](https://arxiv.org/abs/1904.07088).

The code in this repository is intended to work with the versions of p4c, BMv2 and PI referenced in `p4/vm/user-bootstrap.sh`. More recent version are likely to break things.

## Setup

Check out the repository on a clean install of Ubuntu 16.04 and run `./setup.sh` (without sudo). This will install all dependencies and the project itself. Do not run this script on an existing install, it will mess it up!

## Running Mininet Demo

1. Run `make run` in `p4/p4`. This will compile the P4 program and start the switches and mininet.
2. After mininet has started, run `sudo ./start-controllers.sh` in the project root folder in a second terminal. This will start the global controller and the local controllers for each switch in a tmux session.

The local controllers will then start doing topology discovery and MACsec rules are added automatically to the match action tables of the switches. You can then start pinging the virtual hosts from each other in Mininet. The first one or two packets will be lost due to the implementation of MAC learning.

### Starting the controllers manually

If you prefer not to use tmux, start each controller in a separate terminal. Details on the parameters of the controllers is available by running `./controller.py --help`.

1. Start the central controller by running `./controller.py` in folder `controller`
2. Start the local controller for each BMv2 switch by running the following commands in folder `controller_distributed`
- `sudo ./controller.py -a 127.0.0.1:50051 -n s1 -s ipc:///tmp/bmv2-0-notifications.ipc -m 00:00:00:FF:01:01`
- `sudo ./controller.py -a 127.0.0.1:50052 -n s2 -s ipc:///tmp/bmv2-1-notifications.ipc -d 1 -l localhost:52002 -m 00:00:00:FF:02:02`
- `sudo ./controller.py -a 127.0.0.1:50053 -n s3 -s ipc:///tmp/bmv2-2-notifications.ipc -d 2 -l localhost:52003 -m 00:00:00:FF:03:03`
