#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

PLUGIN_CI_LIST=`git ls-files`
PLUGIN_CI_LIST+=" bin/x86_64"
PLUGIN_CI_LIST+=" bin/aarch64"

cd bin/
# x86_64
cargo build --release --target x86_64-unknown-linux-gnu
mkdir -p x86_64
mv -f target/x86_64-unknown-linux-gnu/release/modbus_rtu_slave x86_64 || true
# aarch64
cargo build --release --target aarch64-unknown-linux-gnu
mkdir -p aarch64
mv -f target/aarch64-unknown-linux-gnu/release/modbus_rtu_slave aarch64 || true

echo $PLUGIN_CI_LIST
