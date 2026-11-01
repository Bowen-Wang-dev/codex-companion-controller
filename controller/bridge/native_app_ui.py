"""Bring the already-connected, version-checked desktop App to the front.

This only activates the original App. It neither draws an approval window nor
clicks/answers the App's UI. Native approval lines remain byte-exact passthrough.
"""
from pathlib import Path
import subprocess
import sys


def focus():
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
    from launch_desktop import APP, verify_build
    verify_build()
    # Do not start a different/default session if the original App is gone.
    try:
        running=subprocess.run(['/usr/bin/pgrep','-f','^'+str(APP/'Contents/MacOS/ChatGPT')],
                               capture_output=True,timeout=2)
        if running.returncode:return False
        result=subprocess.run(['/usr/bin/open','-a',str(APP)],capture_output=True,timeout=3)
    except subprocess.TimeoutExpired:return False
    return result.returncode==0
