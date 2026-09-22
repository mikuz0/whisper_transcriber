#!/bin/bash
QT_QPA_PLATFORM=xcb exec "$(dirname "$0")/main" "$@"