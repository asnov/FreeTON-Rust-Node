#!/bin/bash -eE

echo "INFO: install dependencies..."

apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg2 \
    gpg \
    tar \
    cmake \
    build-essential \
    pkg-config \
    libssl-dev \
    libtool \
    m4 \
    automake \
    clang \
    git \
    python3-pip \
    jq

pip3 install jmespath

# This script downloads latest version but 1.45.2 was tested by TONLabs
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y 
