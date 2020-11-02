#!/usr/bin/env python
"""A stripped-down version of Django's command-line utility, for testing only."""
import os
import sys


def main():
    """Run test tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "managair_server.settings")

    # See https://testdriven.io/blog/django-debugging-vs-code/
    import ptvsd

    ptvsd.enable_attach(address=("0.0.0.0", 3001), log_dir=None)
    print("Waiting for external debugger...")
    ptvsd.wait_for_attach()
    print("Attached!")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Sneak in the test command.
    argv = sys.argv
    argv.insert(1, "test")
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
