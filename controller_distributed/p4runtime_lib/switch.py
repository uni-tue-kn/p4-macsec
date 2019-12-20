# Copyright 2017-present Open Networking Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from abc import abstractmethod
from time import sleep
import threading

import grpc
from p4.v1 import p4runtime_pb2
from p4.v1 import p4runtime_pb2_grpc
from p4.tmp import p4config_pb2


class SwitchConnection(object):
    def __init__(self, name, address='127.0.0.1:50051', device_id=0, type='bmv2', crypto_address = None, debug=False):
        self.name = name
        self.address = address
        self.device_id = device_id
        self.p4info = None
        self.channel = grpc.insecure_channel(self.address)
        self.client_stub = p4runtime_pb2_grpc.P4RuntimeStub(self.channel)
        self.type = type
        self.crypto_client = None
        if self.type == 'tofino':
            self.crypto_client = TofinoCryptoClient(crypto_address)
        self.debug = debug
	self.request_lock = threading.Lock()

    @abstractmethod
    def buildDeviceConfig(self, **kwargs):
        return p4config_pb2.P4DeviceConfig()

    def SetForwardingPipelineConfig(self, p4info, dry_run=False, **kwargs):
        device_config = self.buildDeviceConfig(**kwargs)
        request = p4runtime_pb2.SetForwardingPipelineConfigRequest()
        #config = request.configs.add()
        #config.device_id = self.device_id

        request.device_id = self.device_id
        config = request.config

        config.p4info.CopyFrom(p4info)
        config.p4_device_config = device_config.SerializeToString()
        request.action = p4runtime_pb2.SetForwardingPipelineConfigRequest.VERIFY_AND_COMMIT
        if dry_run:
            print "P4 Runtime SetForwardingPipelineConfig:", request
        else:
            self.client_stub.SetForwardingPipelineConfig(request)

    def WriteTableEntry(self, table_entry, dry_run=False):
        request = p4runtime_pb2.WriteRequest()
        request.device_id = self.device_id

        #nur master duerfen writes vornehmen
        request.election_id.low = 1
        request.election_id.high = 0

        update = request.updates.add()
        update.type = p4runtime_pb2.Update.INSERT
        update.entity.table_entry.CopyFrom(table_entry)
        if dry_run:
            print "P4 Runtime Write:", request
        else:
            self.client_stub.Write(request)

    def DeleteTableEntry(self, table_entry, dry_run=False):
        request = p4runtime_pb2.WriteRequest()
        request.device_id = self.device_id

        #nur master duerfen writes vornehmen
        request.election_id.low = 1
        request.election_id.high = 0

        update = request.updates.add()
        update.type = p4runtime_pb2.Update.DELETE
        update.entity.table_entry.CopyFrom(table_entry)
        if dry_run:
            print "P4 Runtime Write:", request
        else:
            self.client_stub.Write(request)

    def ReadTableEntries(self, table_id=None, dry_run=False):
        request = p4runtime_pb2.ReadRequest()
        request.device_id = self.device_id
        entity = request.entities.add()
        table_entry = entity.table_entry
        if table_id is not None:
            table_entry.table_id = table_id
        else:
            table_entry.table_id = 0
        if dry_run:
            print "P4 Runtime Read:", request
        else:
            for response in self.client_stub.Read(request):
                yield response

    def ReadCounters(self, counter_id=None, index=None, dry_run=False):
        request = p4runtime_pb2.ReadRequest()
        request.device_id = self.device_id
        entity = request.entities.add()
        counter_entry = entity.counter_entry
        if counter_id is not None:
            counter_entry.counter_id = counter_id
        else:
            counter_entry.counter_id = 0
        if index is not None:
            counter_entry.index = index
        if dry_run:
            print "P4 Runtime Read:", request
        else:
            for response in self.client_stub.Read(request):
                yield response

    def stringifySerialData(self, data):
        numbers = map(ord,data)
        res = ""
        for n in numbers:
            res = res + ("\\0x{:02x}".format(n))
        return res

    def send_packet_out(self, payload):
        request = p4runtime_pb2.StreamMessageRequest()
        request.packet.payload = payload
	self.request_lock.acquire()
        self.requests.append(request)
	self.request_lock.release()

    def send_packet_out_multiple(self, payloads):
	new_requests = []
	for payload in payloads:
	    request = p4runtime_pb2.StreamMessageRequest()
	    request.packet.payload = payload
            new_requests.append(request)

	self.request_lock.acquire()
        self.requests.extend(new_requests)
	self.request_lock.release()

    def send_init_and_wait(self, response_callback):
        self.waiting = True
	self.request_lock.acquire()
        self.requests = []

        init_req = p4runtime_pb2.StreamMessageRequest()
        init_req.arbitration.election_id.low = 1
        init_req.arbitration.election_id.high = 0
        init_req.arbitration.device_id = self.device_id
        self.requests.append(init_req)
        self.request_lock.release()

        for response in self.client_stub.StreamChannel(self.processRequests()):
            if response_callback is not None:
                response_callback(self, response)
            else:
                if self.debug:
                    print("response: \n"  + str(response))



    def stop_waiting(self):
        self.waiting = False

    def processRequests(self):
        while self.waiting:
	    self.request_lock.acquire()
            if len(self.requests) > 0:
                req = self.requests.pop(0)
                if self.debug:
                    print("sending request to switch %s \n%s" % (self.name, req))
                yield req
	    self.request_lock.release()


            sleep(0.1)
