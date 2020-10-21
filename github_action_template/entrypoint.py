"""Main entrypoint for this action when run as a Docker container."""
import importlib
import os
import sys

from github_action_template.framework import ActionError, GitHubEnvironment


def main() -> int:
    """Just a wrapper to instantiate and call concrete Action implementation."""
    try:
        print(f"::debug::Loading action {sys.argv[1]}")
        # First arg is the FQ python class name, the rest is passed down to the action
        action_fqname = sys.argv[1].split(".")
        module = importlib.import_module(".".join(action_fqname[:-1]))
        class_ = getattr(module, action_fqname[-1])
        action_instance = class_(GitHubEnvironment(os.environ))
        action_instance.debug("Action loaded successfully")
    except Exception as error:  # pylint: disable=W0703
        print(f"::error::Cannot instantiate action '{sys.argv[1]}' because of {error.__class__.__name__}: {error}")
        return 1

    try:
        action_instance.run(sys.argv[2:])
        return 0
    except ActionError as error:
        print(f"::error::Exiting with error code because of action error: {error}")
    except Exception as error:  # pylint: disable=W0703
        print(f"::error::Unexpected error when running action: {error.__class__.__name__}: {error}")
    return 2


if __name__ == '__main__':
    sys.exit(main())
