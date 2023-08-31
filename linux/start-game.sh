#!/bin/sh
cd ..

export LOGIN_TOKEN=dev

venv/bin/python3 -m toontown.launcher.QuickStartLauncher
