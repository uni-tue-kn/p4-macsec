#!/usr/bin/env python2

# Copyright 2018-present University of Tuebingen, Chair of Communication Networks
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

#
# Marco Haeberle (marco.haeberle@uni-tuebingen.de)
# Joshua Hartmann
#
#

import grpc
from concurrent import futures
import time
import sys
import threading
import argparse
import cli

import switch_controller
import topo_client
import control_server

import control_pb2, control_pb2_grpc

# define some variables
ca_path = '../tools/certstrap/out/p4sec-ca.crt'
cert_path = '../tools/certstrap/out/localhost.crt'
key_path = '../tools/certstrap/out/localhost.key'

def start_control_server(switch_controller, listen_addr):
    # create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    control_pb2_grpc.add_ControlServicer_to_server(control_server.ControlServer(switch_controller), server)

    # prepare tls creds
    try:
        with open(ca_path, 'rb') as ca_file:
            ca = ca_file.read()
    except IOError as e:
        #print(e)
        sys.exit("Error opening CA file")

    try:
        with open(cert_path, 'rb') as cert_file:
            cert = cert_file.read()
    except IOError as e:
        #print(e)
        sys.exit("Error opening cert file")

    try:
        with open(key_path, 'rb') as key_file:
            key = key_file.read()
    except IOError as e:
        #print(e)
        sys.exit("Error opening key file")

    server_creds = grpc.ssl_server_credentials([(key, cert)], ca, True)

    # listen on port 50051
    #print('Starting gRPC server. Listening on ' + listen_addr)
    server.add_secure_port(listen_addr, server_creds)
    server.start()

    # server.start() does not block -> sleep-loop to keep the server alive
    while True:
        time.sleep(100)


def start_cli(ctrl):
    print('starting cli')

    cmd = cli.CLI()
    cmd.set_controller(ctrl)
    cmd.cmdloop()

    ctrl.teardown()


parser = argparse.ArgumentParser(description='P4Runtime Controller')
parser.add_argument('--p4info', help='p4info proto in text format from p4c', type=str, action="store", required=False,
                    default='../p4/p4/build/basic.p4info')
parser.add_argument('--bmv2-json', help='BMv2 JSON file from p4c', type=str, action="store", required=False,
                    default='../p4/p4/build/basic.json')
parser.add_argument('-a', help='P4Runtime address', type=str, action="store", required=False,
                    default='127.0.0.1:50051')
parser.add_argument('-s', help='nanomsg socket for notifications from simple_switch', type=str, action="store", required=False,
                    default='ipc:///tmp/bmv2-0-notifications.ipc')
parser.add_argument('-n', help='name of the switch (needs to be unique)', type=str, action="store", required=False,
                    default='s0')
parser.add_argument('-d', help='device id of the switch', type=str, action="store", required=False,
                    default='0')
parser.add_argument('--num-ports', help='number of ports excluding CPU port', type=str, action="store", required=False,
                    default='15')
parser.add_argument('-c', help='address of the central controller', type=str, action="store", required=False,
                    default='localhost:51001')
parser.add_argument('-l', help='listen address for control server', type=str, action="store", required=False,
                    default='localhost:52001')
parser.add_argument('-m', help='mac address of the switch', type=str, action="store", required=False,
                    default='62:88:00:00:00:01')
args = parser.parse_args()

switch_name = args.n
switch_ip = args.a
notification_socket = args.s
device_id = int(args.d)
num_ports = args.num_ports
controller_address = args.c
listen_address = args.l
mac_address = args.m

# grpc client for communication wiht central controller
topo_client = topo_client.TopoClient(controller_address)

# global ctrl
ctrl = switch_controller.SwitchController(args.p4info, args.bmv2_json, topo_client, mac_address)

# grpc server for communication with central controller
control_server_t = threading.Thread(target=start_control_server, args=(ctrl, listen_address))
control_server_t.daemon = True
control_server_t.start()

## BMV2 switches
ctrl.add_switch_connection(switch_name,
                           address=switch_ip,
                           device_id=device_id,
                           debug = False,
                           type = 'bmv2',
                           notification_socket = notification_socket,
                           num_ports = num_ports)
ctrl.startup()

topo_client.registerController(listen_address, switch_name, mac_address)

# cli
cli_t = threading.Thread(target=start_cli, args=(ctrl,))
cli_t.daemon = True
cli_t.start()

# exit when CTRL-C ist pressed or when the CLI is stopped by entering 'exit'
try:
    while cli_t.is_alive():
        time.sleep(1)
    topo_client.updateTopo(switch_name, {})
except KeyboardInterrupt:
    print('shutting down')
    topo_client.updateTopo(switch_name, {})
    sys.exit(0)
