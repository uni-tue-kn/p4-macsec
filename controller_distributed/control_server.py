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

# import generated proto classes
import control_pb2, control_pb2_grpc


class ControlServer(control_pb2_grpc.ControlServicer):
    def __init__(self, switch_controller):
        self.switch_controller = switch_controller

    def addMACsecProtectRule(self, request, context):
        print('add MACsec protect rule, command from ' + str(context.peer_identities()[0]))
        response = control_pb2.control_status()

        switch = self.switch_controller.name2switch[request.switch]
        port = request.port
        key = request.key.encode('ascii', 'ignore')
        system_id = request.systemID.encode('ascii', 'ignore')

        print('\tswitch:\t\t' + request.switch)
        print('\tport:\t\t' + str(port))
        print('\tkey:\t\t' + key)
        print('\tsystemID:\t' + system_id)

        self.switch_controller.writeMACsecRulesProtect(switch, port, key, system_id)

        response.success = True
        return response

    def addMACsecValidateRule(self, request, context):
        print('add MACsec validate rule, command from ' + str(context.peer_identities()[0]))
        response = control_pb2.control_status()

        switch = self.switch_controller.name2switch[request.switch]
        port = request.port
        key = request.key.encode('ascii', 'ignore')

        print('\tswitch:\t' + request.switch)
        print('\tport:\t' + str(port))
        print('\tkey:\t' + key)

        self.switch_controller.writeMACsecRulesValidate(switch, port, key)

        response.success = True
        return response

    def deleteMACsecProtectRule(self, request, context):
        print('delete MACsec protect rule, command from ' + str(context.peer_identities()[0]))
        response = control_pb2.control_status()

        switch = self.switch_controller.name2switch[request.switch]
        port = request.port;

        print('\tswitch:\t' + request.switch)
        print('\tport:\t' + str(port))

        self.switch_controller.deleteMACsecRulesProtect(switch, port)

        response.success = True
        return response

    def deleteMACsecValidateRule(self, request, context):
        print('delete MACsec validate rule, command from ' + str(context.peer_identities()[0]))
        response = control_pb2.control_status()

        switch = self.switch_controller.name2switch[request.switch]
        port = request.port;

        print('\tswitch:\t' + request.switch)
        print('\tport:\t' + str(port))

        self.switch_controller.deleteMACsecRulesValidate(switch, port)

        response.success = True
        return response
