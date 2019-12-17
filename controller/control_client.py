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

import control_pb2
import control_pb2_grpc


class ControlClient:
    def __init__(self, ca_path, cert_path, key_path):
        # prepare tls creds
        try:
            with open(ca_path, 'rb') as ca_file:
                ca = ca_file.read()
        except (FileNotFoundError, PermissionError, IsADirectoryError) as e:
            print(e)
            sys.exit("[E] Error opening CA file")

        try:
            with open(cert_path, 'rb') as cert_file:
                cert = cert_file.read()
        except (FileNotFoundError, PermissionError, IsADirectoryError) as e:
            print(e)
            sys.exit("[E] Error opening cert file")

        try:
            with open(key_path, 'rb') as key_file:
                key = key_file.read()
        except (FileNotFoundError, PermissionError, IsADirectoryError) as e:
            print(e)
            sys.exit("[E] Error opening key file")

        self.client_creds = grpc.ssl_channel_credentials(ca, key, cert)
        self.channels = {}
        self.stubs = {}
        self.id_to_mac = {}

    def createControlStub(self, switch, address):
        self.channels[switch] = grpc.secure_channel(address, self.client_creds)
        self.stubs[switch] = control_pb2_grpc.ControlStub(self.channels[switch])
        print('gRPC stub created for switch ' + switch + ' at ' + address)

    def addMACsecProtectRule(self, switch, port, key):
        if switch not in self.stubs:
            print('Error addMACsecProtectRule: no stub for switch ' + switch)
            return

        request = control_pb2.MACsecProtectRule()

        request.switch = switch
        request.port = port
        request.key = key
        try:
            request.systemID = self.id_to_mac[switch]
        except KeyError:
            print("Error: Can't set MACsec protect rule for switch " + switch + ". MAC address unknown")
            return

        try:
            response = self.stubs[switch].addMACsecProtectRule(request)
        except KeyError:
            print("Error: Can't sent request to " + switch + ". No stub")
            return

        if not response.success:
            print('ERROR control client when adding MACsec protect rule: ' + response.error)
            return False

        return True

    def addMACsecValidateRule(self, switch, port, key):
        if switch not in self.stubs:
            print('Error addMACsecValidateRule: no stub for switch ' + switch)
            return False

        request = control_pb2.MACsecValidateRule()

        request.switch = switch
        request.port = port
        request.key = key

        try:
            response = self.stubs[switch].addMACsecValidateRule(request)
        except KeyError:
            print("Error: Can't sent request to " + switch + ". No stub")
            return

        if not response.success:
            print('ERROR control client when adding MACsec validate rule: ' + response.error)
            return False

        return True

    def deleteMACsecProtectRule(self, switch, port):
        if switch not in self.stubs:
            print('Error deleteMACsecProtectRule: no stub for switch ' + switch)
            return

        request = control_pb2.MACsecProtectRule()

        request.switch = switch
        request.port = port

        try:
            response = self.stubs[switch].deleteMACsecProtectRule(request)
        except KeyError:
            print("Error: Can't sent request to " + switch + ". No stub")
            return

        if not response.success:
            print('ERROR control client when deleting MACsec protect rule: ' + response.error)
            return False

        return True

    def deleteMACsecValidateRule(self, switch, port):
        if switch not in self.stubs:
            print('Error deleteMACsecValidateRule: no stub for switch ' + switch)
            return False

        request = control_pb2.MACsecValidateRule()

        request.switch = switch
        request.port = port

        try:
            response = self.stubs[switch].deleteMACsecValidateRule(request)
        except KeyError:
            print("Error: Can't sent request to " + switch + ". No stub")
            return

        if not response.success:
            print('ERROR control client when deleting MACsec validate rule: ' + response.error)
            return False

        return True
