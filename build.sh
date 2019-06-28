#!/usr/bin/env bash
##########################################################################
#                                                                        #
#  Blackbird: An ontology to relational schema translator                #
#  Copyright (C) 2019 OBDA Systems                                       #
#                                                                        #
#  ####################################################################  #
#                                                                        #
#  This program is free software: you can redistribute it and/or modify  #
#  it under the terms of the GNU General Public License as published by  #
#  the Free Software Foundation, either version 3 of the License, or     #
#  (at your option) any later version.                                   #
#                                                                        #
#  This program is distributed in the hope that it will be useful,       #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the          #
#  GNU General Public License for more details.                          #
#                                                                        #
#  You should have received a copy of the GNU General Public License     #
#  along with this program. If not, see <http://www.gnu.org/licenses/>.  #
#                                                                        #
##########################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$SCRIPT_DIR"
BUILD_DIR="${BUILD_DIR:-$SCRIPT_DIR/build}"
INSTALL_DIR="${INSTALL_DIR:-${HOME}/.eddy/plugins/blackbird}"

_usage() {
    echo "usage $0: Blackbird plugin builder script"
    echo
    echo "Supported arguments:"
    echo "    clean   - clean up build and temporary files"
    echo "    install - install the plugin locally [default: ~/.eddy/plugins]"
    echo "    package - build a redistributable .zip plugin bundle"
}

_spec() {
    [[ $# -lt 1 ]] && return
    cat "$ROOT_DIR/plugin.spec" | awk "/$1:/ { print \$2 }"
}

_clean() {
    rm -rf "$BUILD_DIR"
}

_install() {
    echo "Installing plugin into $INSTALL_DIR..."
    mkdir -p "$INSTALL_DIR"
    cp -a "$ROOT_DIR/blackbird" "$INSTALL_DIR"
    cp -a "$ROOT_DIR/plugin.spec" "$INSTALL_DIR"
    cp -a "$ROOT_DIR/LICENSE" "$INSTALL_DIR"
    if [[ -f "$ROOT_DIR/blackbird.jar" ]]; then
        cp -a "$ROOT_DIR/blackbird.jar" "$INSTALL_DIR"
    fi
}

_package() {
    local version=$(_spec version)
    local zipfile="$BUILD_DIR/blackbird-${version}.zip"
    local install_dir="$BUILD_DIR/blackbird-${version}"
    INSTALL_DIR="${install_dir}" _install
    echo "Packaging project into $zipfile"
    cd "$BUILD_DIR" && zip $(basename "$zipfile") -rq "blackbird-${version}" -x \*.pyc \*.pyo __pycache__
}

if [[ $# -lt 1 ]]; then
    _usage
    exit 1
fi

case "$1" in
    clean) _clean;;
    spec) _spec "$2";;
    install) _install;;
    package) _package;;
    *) usage; exit 1;;
esac

exit 0
