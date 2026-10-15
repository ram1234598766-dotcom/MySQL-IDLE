#!/usr/bin/env bash
# Build the official CPython 3.15.0 source release with a verified archive hash.
# Used by Linux CI while managed interpreter mirrors catch up with the final release.
set -euo pipefail

version="3.15.0"
archive_sha256="ba4bed1ba346b916890b76d9e320451420aa69f6408997d33c66482eeae3d575"
archive="${RUNNER_TEMP:?}/Python-${version}.tar.xz"
build_root="${RUNNER_TEMP}/cpython-${version}-build"
prefix="${RUNNER_TEMP}/python-${version}"
venv="${GITHUB_WORKSPACE:?}/.venv"

sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  build-essential ca-certificates curl libbz2-dev libffi-dev libgdbm-dev \
  libgdbm-compat-dev liblzma-dev libncursesw5-dev libreadline-dev \
  libsqlite3-dev libssl-dev pkg-config tk-dev uuid-dev xz-utils zlib1g-dev

curl --fail --location --retry 3 \
  "https://www.python.org/ftp/python/${version}/Python-${version}.tar.xz" \
  --output "$archive"
printf '%s  %s\n' "$archive_sha256" "$archive" | sha256sum --check -

mkdir -p "$build_root" "$prefix"
tar -xJf "$archive" -C "$build_root"
cd "$build_root/Python-${version}"
./configure --prefix="$prefix" --with-ensurepip=install
make -j"$(nproc)"
make install

"$prefix/bin/python3.15" --version
"$prefix/bin/python3.15" -m venv "$venv"
echo "$venv/bin" >> "$GITHUB_PATH"
"$venv/bin/python" --version
