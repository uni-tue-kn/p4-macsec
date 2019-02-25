#!/bin/bash

git clone https://github.com/CESNET/libyang.git
cd libyang
git checkout v0.16-r1
mkdir build
cd build
cmake ..
make
sudo make install
sudo ldconfig
cd ../../

git clone https://github.com/sysrepo/sysrepo.git
cd sysrepo
git checkout v0.7.5
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_EXAMPLES=Off -DCALL_TARGET_BINS_DIRECTLY=Off ..
make
sudo make install
sudo ldconfig

cd ../../

