all: topo_pb2.py topo_pb2_grpc.py control_pb2.py control_pb2_grpc.py

topo_pb2.py topo_pb2_grpc.py: topo.proto
	python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. topo.proto

control_pb2.py control_pb2_grpc.py: control.proto
	python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. control.proto

controller: topo_pb2.py topo_pb2_grpc.py control_pb2.py control_pb2_grpc.py
	cp topo_pb2_grpc.py ../controller
	cp topo_pb2.py ../controller
	cp control_pb2_grpc.py ../controller
	cp control_pb2.py ../controller

controller_distributed: topo_pb2.py topo_pb2_grpc.py control_pb2.py control_pb2_grpc.py
	cp topo_pb2.py ../controller_distributed
	cp topo_pb2_grpc.py ../controller_distributed
	cp control_pb2_grpc.py ../controller_distributed
	cp control_pb2.py ../controller_distributed

clean:
	rm -f client_pb2_grpc.py
	rm -f client_pb2.py
	rm -f tofino_crypto_pb2.py
	rm -f no_crypto_pb2_grpc.py
