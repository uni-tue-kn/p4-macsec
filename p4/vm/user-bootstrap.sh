#!/bin/bash

# Print script commands.
set -x
# Exit on errors.
set -e

#BMV2_COMMIT="39abe290b4143e829b8f983965fcdc711e3c450c"
BMV2_COMMIT="ae87b4d4523488ac935133b4aef437796ad1bbd1"

#PI_COMMIT="1ca80066e065ae52a34416822c20b83173b2146f"
PI_COMMIT="a3d905b14fb151a6752adc076902c9cb75f719ef"

#P4C_COMMIT="e737c57d1dd32b2daaaecf0bc17bb475b14bdf4c"
#P4C_COMMIT="6070b20a6ca83bc6c66c6aac2ea53f83df1c8c61"
#P4C_COMMIT="5f948527dc9f67525b5d0067dc33365f3c6c669b"
P4C_COMMIT="04c02d5eab53fbfc35a4dfca5bfeeeeaa378456a"

PROTOBUF_COMMIT="v3.5.2"
GRPC_COMMIT="v1.3.2"

NUM_CORES=`grep -c ^processor /proc/cpuinfo`

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
  cmake -DPC_LIBGMP_LIBDIR="/usr/lib/x86_64-linux-gnu/" ..
  make -j${NUM_CORES}
  sudo make install
  sudo ldconfig
  cd ..
  cd ..
else
  echo "p4c already exists"
fi
