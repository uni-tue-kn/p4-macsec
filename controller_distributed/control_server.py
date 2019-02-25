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
