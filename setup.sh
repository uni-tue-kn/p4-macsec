#!/bin/bash

# Print script commands.
set -x
# Exit on errors.
set -e

# Set-up P4 environment
cd p4/vm
sudo ./root-bootstrap.sh
./libyang-sysrepo.sh
./user-bootstrap.sh
cd ../..

# Replace simple_switch.cpp of BMv2 with modified version
cp p4/simple_switch.cpp p4/vm/behavioral-model/targets/simple_switch/simple_switch.cpp
cd p4/vm/behavioral-model/targets/simple_switch
# Add -lcrypto to LIBS in Makefiles of simple_switch and simple_switch_grpc and compile
sed -i -E 's/^LIBS =(.*)/LIBS=\1 -lcrypto/g' Makefile
make
cd ../simple_switch_grpc
sed -i -E 's/^LIBS =(.*)/LIBS=\1 -lcrypto/g' Makefile
make
cd ../../../../..
