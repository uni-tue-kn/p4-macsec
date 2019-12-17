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
#
#

import grpc
from concurrent import futures
import time
import sys
import threading
import argparse
import cli

# import generated proto classes
import topo_pb2, topo_pb2_grpc

import topo_server
import control_client

# define some variables
ca_path = '../tools/certstrap/out/p4sec-ca.crt'
cert_path = '../tools/certstrap/out/localhost.crt'
key_path = '../tools/certstrap/out/localhost.key'
listen_addr = '0.0.0.0:51001'


def start_topo_server(topo, control_client):
    # create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    topo_pb2_grpc.add_TopoServiceServicer_to_server(topo_server.TopoServer(topo, control_client), server)

    # prepare tls creds
    try:
        with open(ca_path, 'rb') as ca_file:
            ca = ca_file.read()
    except IOError as e:
        print(e)
        sys.exit("Error opening CA file")

    try:
        with open(cert_path, 'rb') as cert_file:
            cert = cert_file.read()
    except IOError as e:
        print(e)
        sys.exit("Error opening cert file")

    try:
        with open(key_path, 'rb') as key_file:
            key = key_file.read()
    except IOError as e:
        print(e)
        sys.exit("Error opening key file")

    server_creds = grpc.ssl_server_credentials([(key, cert)], ca, True)

    # listen on port 50051
    print('Starting gRPC server for clients. Listening on ' + listen_addr)
    server.add_secure_port(listen_addr, server_creds)
    server.start()

    # server.start() does not block -> sleep-loop to keep the server alive
    while True:
        time.sleep(100)


def start_cli(topo, control_client):
    print('starting cli')

    cmd = cli.CLI()
    cmd.set_topo(topo)
    cmd.set_control_client(control_client)
    cmd.cmdloop()


# parser = argparse.ArgumentParser(description='P4Runtime Controller')
# parser.add_argument('--p4info', help='p4info proto in text format from p4c', type=str, action="store", required=False,
#                     default='../p4/p4/build/basic.p4info')
# parser.add_argument('--bmv2-json', help='BMv2 JSON file from p4c', type=str, action="store", required=False,
#                     default='../p4/p4/build/basic.json')
# args = parser.parse_args()

control_client = control_client.ControlClient(ca_path, cert_path, key_path)

topo = {}

topo_t = threading.Thread(target=start_topo_server, args=(topo,control_client))
topo_t.daemon = True
topo_t.start()

cli_t = threading.Thread(target=start_cli, args=(topo, control_client))
cli_t.daemon = True
cli_t.start()

# exit when CTRL-C ist pressed or when the CLI is stopped by entering 'exit'
try:
    while cli_t.is_alive():
        time.sleep(1)
except KeyboardInterrupt:
    print('shutting down')
    sys.exit(0)
