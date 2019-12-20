#!/bin/bash

# Print commands and exit on errors
set -xe

apt-get update

DEBIAN_FRONTEND=noninteractive apt-get -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" upgrade

apt-get install -y --no-install-recommends \
  autoconf \
  autoconf-archive \
  automake \
  bison \
  build-essential \
  ca-certificates \
  cmake \
  cpp \
  curl \
  flex \
  git \
  libboost-dev \
  libboost-filesystem-dev \
  libboost-iostreams-dev \
  libboost-program-options-dev \
  libboost-system-dev \
  libboost-test-dev \
  libboost-thread-dev \
  libc6-dev \
  libevent-dev \
  libffi-dev \
  libfl-dev \
  libgc-dev \
  libgc1c2 \
  libgflags-dev \
  libgmp-dev \
  libgmp10 \
  libgmpxx4ldbl \
  libjudy-dev \
  libpcap-dev \
  libpthread-stubs0-dev \
  libreadline-dev \
  libssl-dev \
  libtool \
  make \
  coreutils \
  pkg-config \
  python \
  python-dev \
  python-ipaddr \
  python-pip \
  python-setuptools \
  tcpdump \
  unzip \
  vim \
  wget \
  xterm \
  libpcre3-dev \
  libavl-dev \
  libev-dev \
  libcmocka-dev \
  swig \
  python-psutil \
  libprotobuf-c-dev \
  protobuf-c-compiler \
  python-ply \
  python3-pip \
  python3-setuptools \
  tmux

#ln -s /usr/lib/x86_64-linux-gnu/libcrypto.so.1.1 /usr/lib/x86_64-linux-gnu/libcrypto.so.6
#ln -s /usr/lib/x86_64-linux-gnu/libssl.so.1.1 /usr/lib/x86_64-linux-gnu/libssl.so.6
