#!/bin/bash

# Print script commands.
set -x
# Exit on errors.
set -e

BMV2_COMMIT="9ef324838b29419040b4f677a3ff65bc72405c44"
PI_COMMIT="1539ecd8a50c159b011d9c5a9c0eba99f122a845"
P4C_COMMIT="afb501c85159bb511650759eaf6aa8e259d37827"

PROTOBUF_COMMIT="v3.6.1"
GRPC_COMMIT="v1.17.2"

NUM_CORES=`grep -c ^processor /proc/cpuinfo`

# Install additional python packages
sudo pip3 install scapy ply
sudo pip install grpcio protobuf cryptography scapy

# Mininet

if [ ! -d "mininet" ]; then
  git clone git://github.com/mininet/mininet mininet
  cd mininet
  sudo ./util/install.sh -nwv
  cd ..
else
  echo "mininet already exists"
fi

# Protobuf
if [ ! -d "protobuf" ]; then
  git clone https://github.com/google/protobuf.git
  cd protobuf
  git checkout ${PROTOBUF_COMMIT}
  export CFLAGS="-Os"
  export CXXFLAGS="-Os"
  export LDFLAGS="-Wl,-s"
  ./autogen.sh
  ./configure --prefix=/usr/local
  make -j${NUM_CORES}
  sudo make install
  sudo ldconfig
  unset CFLAGS CXXFLAGS LDFLAGS
  cd ..
else
  echo "protobuf already exists"
fi

# gRPC
if [ ! -d "grpc" ]; then
  git clone https://github.com/grpc/grpc.git
  cd grpc
  git checkout ${GRPC_COMMIT}
  git submodule update --init
  export LDFLAGS="-Wl,-s"
  make -j${NUM_CORES}
  sudo make install
  sudo ldconfig
  unset LDFLAGS
  cd ..
else
  echo "grpc already exists"
fi
# Install gRPC Python Package
sudo pip install grpcio
bm_installed=false
# BMv2 deps (needed by PI)
if [ ! -d "behavioral-model" ]; then
  git clone https://github.com/p4lang/behavioral-model.git
  cd behavioral-model
  git checkout ${BMV2_COMMIT}
  # From bmv2's install_deps.sh, we can skip apt-get install.
  # Nanomsg is required by p4runtime, p4runtime is needed by BMv2...
  tmpdir=`mktemp -d -p .`
  cd ${tmpdir}
  bash ../travis/install-thrift.sh
  bash ../travis/install-nanomsg.sh
  sudo ldconfig
  bash ../travis/install-nnpy.sh
  cd ..
  sudo rm -rf $tmpdir
  cd ..
  bm_installed=true
else
  echo "behavioral-model already exists"
fi
echo $bm_installed
# PI/P4Runtime
if [ ! -d "PI" ]; then
  git clone https://github.com/p4lang/PI.git
  cd PI
  git checkout ${PI_COMMIT}
  git submodule update --init --recursive
  ./autogen.sh
  ./configure --with-proto
  make -j${NUM_CORES}
  sudo make install
  sudo ldconfig
  cd ..
else
  echo "PI already exists"
fi
# Bmv2
if [ "$bm_installed" = true ]; then
  cd behavioral-model
  ./autogen.sh
  ./configure --enable-debugger --with-pi
  make -j${NUM_CORES}
  sudo make install
  sudo ldconfig
  # Simple_switch_grpc target
  cd targets/simple_switch_grpc
  ./autogen.sh
  ./configure
  make -j${NUM_CORES}
  sudo make install
  sudo ldconfig
  cd ..
  cd ..
  cd ..
else
  echo "bm didn't got installed"
fi
# P4C
if [ ! -d "p4c" ]; then
  git clone https://github.com/p4lang/p4c
  cd p4c
  git checkout ${P4C_COMMIT}
  git submodule update --init --recursive
  mkdir -p build
  cd build
  cmake ..
  make -j${NUM_CORES}
  sudo make install
  sudo ldconfig
  cd ..
  cd ..
else
  echo "p4c already exists"
fi

