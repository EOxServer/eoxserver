import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "autotest.settings")

    from django.core.management import execute_from_command_line

    # Initialize the EOxServer component system.
    import eoxserver.core
    eoxserver.core.initialize()
    
    execute_from_command_line(sys.argv)
