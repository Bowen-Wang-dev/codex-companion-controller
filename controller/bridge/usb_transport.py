"""Open USB without deliberately asserting reset control lines."""


def open_usb(port, serial):
    device = serial.Serial(port=None, baudrate=115200, timeout=.1, write_timeout=1, exclusive=True)
    device.dtr = False
    device.rts = False
    device.port = port
    try:
        device.open()
    except BaseException as error:
        device.close()
        # macOS termios.error does not inherit OSError. Normalize only this
        # specific OS error so the Bridge can keep Wi-Fi running.
        try:
            import termios
        except ImportError:
            termios = None
        if termios is not None and isinstance(error, termios.error):
            code = error.args[0] if error.args and isinstance(error.args[0], int) else 5
            message = str(error.args[1]) if len(error.args) > 1 else str(error)
            raise OSError(code, message) from error
        raise
    return device
