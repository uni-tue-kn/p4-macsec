# P4-MACsec

This projects implements MACsec in BMv2 together with an automated, controller based set-up of MACsec connections. The automated set-up uses a topology discovery using an enhanced version of LLDP that encrypts LLDP payloads. For details, please see the corresponding [paper](https://arxiv.org/abs/1904.07088).

The code in this repository is intended to work with the versions of p4c, BMv2 and PI referenced in `p4/vm/user-bootstrap.sh`. More recent version are likely to break things.

## Installation

The following instruction is intended to be run on a clean install of Ubuntu 16.04.

Install the P4 environment by changing into the folder `p4/vm` and executing the scripts `root-bootstrap.sh`, `libyang-sysrepo.sh` and `user-bootstrap.sh`.

```
cd p4/vm
sudo ./root-bootstrap.sh
./libyang-sysrepo.sh
./user-bootstrap.sh
```

Apply modifications to the BMv2 `simple_switch` and `simple_switch_grpc` targets.

1. Copy `simple_switch.cpp` from `p4/target` to `p4/vm/behavioral-model/targets/simple_switch/`
2. Add `-lcrypto` to `LIBS` in `p4/vm/behavioral-model/targets/simple_switch/Makefile`
3. Run `make` in `p4/vm/behavioral-model/targets/simple_switch/`
4. Add `-lcrypto` to `LIBS` in `p4/vm/behavioral-model/targets/simple_switch_grpc/Makefile`
5. Run `make` in `p4/vm/behavioral-model/targets/simple_switch_grpc/`

Install dependencies for the controllers:

1.
    ```
    sudo pip install grpc
    sudo pip install protobuf
    sudo pip install cryptography
    ```
2. `sudo pip install --upgrade scapy`
3. `sudo apt remove python-scapy`

## Running Mininet Demo

1. Run `make run` in `p4/p4`. If the P4 program is recompiled, you need to add the extern_instance definition to the generated json file manually and then run `make run` again. See subsection 'extern_instances' below.
2. Start central controller by running `./controller.py` in folder `controller`
3. Start the local controller for each BMv2 switch by running the following commands in folder `controller_distributed`
- `sudo ./controller.py -a 127.0.0.1:50051 -n s1 -s ipc:///tmp/bmv2-0-notifications.ipc -m 00:00:00:FF:01:01`
- `sudo ./controller.py -a 127.0.0.1:50052 -n s2 -s ipc:///tmp/bmv2-1-notifications.ipc -d 1 -l localhost:52002 -m 00:00:00:FF:02:02`
- `sudo ./controller.py -a 127.0.0.1:50053 -n s3 -s ipc:///tmp/bmv2-2-notifications.ipc -d 2 -l localhost:52003 -m 00:00:00:FF:03:03`

The local controllers will then start doing topology discovery and MACsec rules are added automatically to the match action tables of the switches. You can then start pinging the virtual hosts from each other in Mininet. The first one or two packets will be lost due to the implementation of MAC learning.

### extern_instances

The p4c compiler version that was used for this project is not able to generate instances of the MACsec externs. You need to replace `"extern_instances" : [],` in `p4/p4/build/basic.json` with the following snippet after compiling the P4 program.

```
  "extern_instances" : [
    {
      "name" : "crypt",
      "id": 0,
      "type": "ext_crypt"

    }
  ],
```
