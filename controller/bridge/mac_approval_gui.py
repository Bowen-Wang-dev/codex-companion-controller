"""Retired standalone UI: inert entrypoint for already-running old Brokers.

Native approvals belong to the original desktop App. This file intentionally
creates no window, including when an old Broker invokes it as a subprocess.
"""


def launch(request_id):
    return None
