"""Native Windows executable entry into the shared transparent stdio relay."""
import os
import sys
from stdio_relay import main

if __name__ == '__main__':
    try:
        real = os.environ['PASSPORT_REAL_CODEX']
        sys.argv[1:] = ['--real', real, '--', *sys.argv[1:]]
        sys.exit(main())
    except (KeyError, OSError, ValueError) as error:
        print('Passport App relay: '+str(error), file=sys.stderr)
        sys.exit(1)
