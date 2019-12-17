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

# import generated proto classes
import topo_pb2, topo_pb2_grpc
import grpc

import cPickle
import os
from threading import Lock

class DictDiffer(object):
    """
    Calculate the difference between two dictionaries as:
    (1) items added
    (2) items removed
    (3) keys same in both but changed values
    (4) keys same in both and unchanged values

    source: https://stackoverflow.com/questions/1165352/calculate-difference-in-keys-contained-in-two-python-dictionaries
    """
    def __init__(self, current_dict, past_dict):
        self.current_dict, self.past_dict = current_dict, past_dict
        self.set_current, self.set_past = set(current_dict.keys()), set(past_dict.keys())
        self.intersect = self.set_current.intersection(self.set_past)
    def added(self):
        return self.set_current - self.intersect
    def removed(self):
        return self.set_past - self.intersect
    def changed(self):
        return set(o for o in self.intersect if self.past_dict[o] != self.current_dict[o])
    def unchanged(self):
        return set(o for o in self.intersect if self.past_dict[o] == self.current_dict[o])


class TopoServer(topo_pb2_grpc.TopoServiceServicer):
    def __init__(self, topo, control_client):
        self.topo = topo
        self.control_client = control_client
        self.key_bddp = os.urandom(32).encode('hex')
        self.macsec_connections = {}
        self.macsec_update_lock = Lock()

    def updateTopo(self, request, context):
        print('topo updated by: ' + str(context.peer_identities()[0]))
        response = topo_pb2.status()

        switch = request.switch.encode('ascii','ignore')
        switch_topo = cPickle.loads(request.topo)

        self.macsec_update_lock.acquire()

        try:
            if switch not in self.topo:
                self.topo[switch] = {}

            d = DictDiffer(switch_topo, self.topo[switch])
            #check if a connection was added
            added = d.added()
            for port in added:
                if (switch in self.control_client.stubs and switch_topo[port]['chassis'] in self.control_client.stubs
                    and (switch not in self.macsec_connections or switch_topo[port]['chassis'] not in self.macsec_connections[switch])
                    and (switch_topo[port]['chassis'] not in self.macsec_connections or switch not in self.macsec_connections[switch_topo[port]['chassis']])):

                        print("added connection from switch " + switch + " port " + str(port) + " to switch " + switch_topo[port]['chassis'] + " port " + str(switch_topo[port]['port']))

                        if switch not in self.macsec_connections:
                            self.macsec_connections[switch] = {}
                        self.macsec_connections[switch][switch_topo[port]['chassis']] = {}
                        self.macsec_connections[switch][switch_topo[port]['chassis']]['port_local'] = port
                        self.macsec_connections[switch][switch_topo[port]['chassis']]['port_remote'] = switch_topo[port]['port']

                        key1 = os.urandom(16).encode('hex')
                        key2 = os.urandom(16).encode('hex')
                        success = self.control_client.addMACsecProtectRule(switch, port, key1)
                        success = success and self.control_client.addMACsecProtectRule(switch_topo[port]['chassis'], switch_topo[port]['port'], key2)
                        success = success and self.control_client.addMACsecValidateRule(switch, port, key2)
                        success = success and self.control_client.addMACsecValidateRule(switch_topo[port]['chassis'], switch_topo[port]['port'], key1)
                        if success:
                            print("\tMACsec rules added to switches")
                        else:
                            print("\tERROR: MACsec rules not added to switches")


            #check if a connection was removed
            removed = d.removed()
            for port in removed:
                print("removed connection from switch " + switch + " port " + str(port) + " to switch " + self.topo[switch][port]['chassis'] + " port " + str(self.topo[switch][port]['port']))
                if switch in self.control_client.stubs and self.topo[switch][port]['chassis'] in self.control_client.stubs:
                    print("stubs known")
                    delete = False
                    print(self.macsec_connections)
                    if switch in self.macsec_connections and self.topo[switch][port]['chassis'] in self.macsec_connections[switch]:
                        print("case 1")
                        switch1 = switch
                        port1 = port
                        switch2 = self.topo[switch][port]['chassis']
                        port2 = self.topo[switch][port]['port']
                        delete = True
                        print("\t" + switch1 + " " + str(port1) + " -> " + switch2 + " " + str(port2))

                    elif self.topo[switch][port]['chassis'] in self.macsec_connections and switch in self.macsec_connections[self.topo[switch][port]['chassis']]:
                        print("case 2")
                        switch1 = self.topo[switch][port]['chassis']
                        port1 = self.topo[switch][port]['port']
                        switch2 = switch
                        port2 = port
                        delete = True
                        print("\t" + switch1 + " " + str(port1) + " -> " + switch2 + " " + str(port2))

                    if delete:
                        success = True
                        try:
                            success = success and self.control_client.deleteMACsecProtectRule(switch1, port1)
                        except grpc.RpcError:
                            print("\tCan't delete MACsec protect rule from switch " + switch1 + "! Maybe the correpsinding controller is down.")

                        try:
                            success = success and self.control_client.deleteMACsecProtectRule(switch2, port2)
                        except grpc.RpcError:
                            print("\tCan't delete MACsec protect rule from switch " + switch2 + "! Maybe the correpsinding controller is down.")

                        try:
                            success = success and self.control_client.deleteMACsecValidateRule(switch1, port1)
                        except grpc.RpcError:
                            print("\tCan't delete MACsec validate rule from switch " + switch1 + "! Maybe the correpsinding controller is down.")

                        try:
                            success = success and self.control_client.deleteMACsecValidateRule(switch2, port2)
                        except grpc.RpcError:
                            print("\tCan't delete MACsec validate rule from switch " + switch2 + "! Maybe the correpsinding controller is down.")

                        if success:
                            print("\tMACsec rules removed from switches")
                        else:
                            print("\tERROR: MACsec rules not removed from switches")

                        del self.macsec_connections[switch1][switch2]

                    else:
                        print("\tMACsec connection not existing, not removing")

            self.topo[switch] = switch_topo

        except:
            print("ERROR!!! Somthing bad happened! Please debug!")

        self.macsec_update_lock.release()

        response.success = True
        return response

    def registerController(self, request, context):
        print('new distributed controller registered: ' + str(context.peer_identities()[0]))
        response = topo_pb2.registerID()

        address = request.address
        switch = request.switch
        mac = request.mac

        print("\taddress:\t" + address)
        print("\tswitch:\t\t" + switch)
        print("\tmac:\t\t" + mac)

        self.control_client.createControlStub(switch, address)
        self.control_client.id_to_mac[switch] = mac

        response.status.success = True
        response.key = bytes(bytearray.fromhex(self.key_bddp))
        return response
