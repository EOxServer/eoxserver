import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "autotest.settings")

    import django
    import eoxserver.core
    from django.core.management import execute_from_command_line

    # Initialize Django apps
    django.setup()

    # Initialize the EOxServer component system.
    eoxserver.core.initialize()
    
    execute_from_command_line(sys.argv)
