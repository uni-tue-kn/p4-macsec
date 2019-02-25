import grpc
import cPickle

import topo_pb2
import topo_pb2_grpc

ca_path = '../tools/certstrap/out/p4sec-ca.crt'
cert_path = '../tools/certstrap/out/localhost.crt'
key_path = '../tools/certstrap/out/localhost.key'

class TopoClient:
    def __init__(self, address):
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

        client_creds = grpc.ssl_channel_credentials(ca, key, cert)
        self.channel = grpc.secure_channel(address, client_creds)
        self.stub = topo_pb2_grpc.TopoServiceStub(self.channel)
        self.key_bddp = None

    def updateTopo(self, switch, topo):
        request = topo_pb2.topo()

        request.switch = switch
        request.topo = cPickle.dumps(topo, cPickle.HIGHEST_PROTOCOL)
        response = self.stub.updateTopo(request)

        if not response.success:
            print('ERROR topo client: ' + response.error)
        else:
            print('Topology update at controller successfull')

    def registerController(self, address_local, switch, mac_switch):
        request = topo_pb2.controller()

        request.address = address_local
        request.switch = switch
        request.mac = mac_switch

        response = self.stub.registerController(request)

        if not response.status.success:
            print('ERROR topo client when registering at central controller: ' + response.error)
        else:
            self.key_bddp = response.key
            print('Controller successfully registered at central controller')
