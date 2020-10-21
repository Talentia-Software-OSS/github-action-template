"""Define a small GitHub action framework with classes like GitHubEnvironment or GitHubAction."""
import json
import secrets
import string
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Optional

from github3 import GitHub, github

# Don't worry this is just a string as random and unique as possible, not a security secret in any way
_DEFAULT_TOKEN = "iop@efà@€@àfea@f@v@vekvevà@hdlizwhkl;vdciev"
EVENT_PULL_REQUEST = "pull_request"


class GitHubEnvironment:  # pylint: disable=R0904
    """
    Provides access to GitHub environment variables and action context such as event payload.
    See https://docs.github.com/en/actions/reference/environment-variables
    """

    def __init__(self, env: Dict[str, str]):
        self.env = env
        self._cached_json_payload = None

    def _mandatory_str(self, key) -> str:
        """Return value of an environment variable that should be defined, or raise an ActionError."""
        try:
            return self.env[key]
        except KeyError:
            raise ActionError(f"Missing environment variable value for {key}")

    @property
    def home(self) -> Path:
        """The path to the GitHub home directory used to store user data. For example, /github/home."""
        return Path(self.env.get("HOME", "."))

    @property
    def workflow(self) -> str:
        """The name of the workflow."""
        return self._mandatory_str("GITHUB_WORKFLOW")

    @property
    def run_id(self) -> str:
        """
        A unique number for each run within a repository.

        This number does not change if you re-run the workflow run.
        """
        return self._mandatory_str("GITHUB_RUN_ID")

    @property
    def run_number(self) -> int:
        """
        A unique number for each run of a particular workflow in a repository.

        This number begins at 1 for the workflow's first run, and increments with each new run.
        This number does not change if you re-run the workflow run.
        """
        try:
            return int(self.env.get("GITHUB_RUN_NUMBER", "1"))
        except ValueError as error:
            raise ActionError("Incorrect environment variable run number value") from error

    @property
    def action(self) -> str:
        """The unique identifier (id) of the action."""
        return self._mandatory_str("GITHUB_ACTION")

    @property
    def actions(self) -> bool:
        """
        Always set to true when GitHub Actions is running the workflow.

        You can use this variable to differentiate when tests are being run locally or by GitHub Actions.
        """
        return self.env.get("GITHUB_ACTIONS", "False").lower() == "true"

    @property
    def actor(self) -> str:
        """The name of the person or app that initiated the workflow. For example, octocat."""
        return self._mandatory_str("GITHUB_ACTOR")

    @property
    def repository(self) -> str:
        """The owner and repository name. For example, octocat/Hello-World."""
        return self._mandatory_str("GITHUB_REPOSITORY")

    @property
    def event_name(self) -> Optional[str]:
        """The name of the webhook event that triggered the workflow."""
        return self._mandatory_str("GITHUB_EVENT_NAME")

    @property
    def event_path(self) -> Path:
        """The path of the file with the complete webhook event payload. For example, /github/workflow/event.json."""
        return Path(self.env.get("GITHUB_EVENT_PATH", "event.json"))

    @property
    def workspace(self) -> Path:
        """
        The GitHub workspace directory path.

        The workspace directory contains a subdirectory with a copy of your repository if your workflow uses the
        actions/checkout action. If you don't use the actions/checkout action, the directory will be empty.
        For example, /home/runner/work/my-repo-name/my-repo-name.
        """
        return Path(self.env.get("GITHUB_WORKSPACE", "."))

    @property
    def sha(self) -> Optional[str]:
        """The commit SHA that triggered the workflow. For example, ffac537e6cbbf934b08745a378932722df287a53."""
        return self.env.get("GITHUB_SHA", None)

    @property
    def ref(self) -> Optional[str]:
        """
        The branch or tag ref that triggered the workflow. For example, refs/heads/feature-branch-1.

        If neither a branch or tag is available for the event type, the variable will not exist.
        """
        return self.env.get("GITHUB_REF", None)

    @property
    def head_ref(self) -> Optional[str]:
        """Only set for forked repositories. The branch of the head repository."""
        return self.env.get("GITHUB_HEAD_REF", None)

    @property
    def base_ref(self) -> Optional[str]:
        """Only set for forked repositories. The branch of the base repository."""
        return self.env.get("GITHUB_BASE_REF", None)

    @property
    def server_url(self) -> str:
        """Returns the URL of the GitHub server. For example: https://github.com."""
        return self._mandatory_str("GITHUB_SERVER_URL")

    @property
    def api_url(self) -> str:
        """Returns the API URL. For example: https://api.github.com."""
        return self._mandatory_str("GITHUB_API_URL")

    @property
    def graphql_url(self) -> str:
        """Returns the GraphQL API URL. For example: https://api.github.com/graphql."""
        return self._mandatory_str("GITHUB_GRAPHQL_URL")

    @property
    def secret_token(self) -> str:
        """
        The GITHUB_TOKEN secret is a GitHub App installation access token.

        You can use the installation access token to authenticate on behalf of the GitHub App installed on your
        repository.
        see https://docs.github.com/en/actions/reference/authentication-in-a-workflow#about-the-github_token-secret
        """
        return self._mandatory_str("GITHUB_TOKEN")

    @property
    def event_payload(self) -> Dict[str, Any]:
        """
        Read event payload data from GitHub-provided JSON file.

        :return: the result of JSON parsing as Python objects
        """
        # This is not thread safe, but actions are supposed to be run as a command-line execution.
        if not self._cached_json_payload:
            try:
                with self.event_path.open() as json_file:
                    self._cached_json_payload = json.load(json_file)
            except (OSError, ValueError) as error:
                raise ActionError("Cannot get event payload data") from error

        return self._cached_json_payload

    def event_payload_find(self, path: str, default: Optional[Any] = None) -> Optional[Any]:
        """
        Safely walk through event payload JSON tree to find a value for a given path.

        :param path: slash-separated (case-sensitive) property names
        :param default: optional default value if requested path does not empty or is empty
        :return: piece of json at given path, or either None or default value if given
        """
        return json_find(self.event_payload, path, default)

    def get(self, var_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get environment variable value, or default value.

        :param var_name: an environment variable name
        :param default: default value if environment variable is not defined
        :return: environment variable value or default value
        """
        return self.env.get(var_name, default)


class GitHubAction:
    """
    Superclass for a GitHub action to be implemented in Python.

    Provides a very basic framework for actions and a few utility methods.
    """

    def __init__(self, github_env: GitHubEnvironment):
        self.github_env = github_env
        self._github_api: Optional[GitHub] = None

    @property
    def github_api(self) -> GitHub:
        """
        See API documentation here https://github3py.readthedocs.io/en/master/api-reference/index.html

        :return: a GitHub API client object, or raise an ActionError if connection fails
        """
        # This is not thread safe, but actions are supposed to be run as a command-line execution.
        if not self._github_api:
            self._github_api = GitHub(token=self.github_env.secret_token)
        return self._github_api

    @staticmethod
    def set_env(name: str, value: str):
        """
        Creates or updates an environment variable for any actions running next in a job.

        The action that creates or updates the environment variable does not have access to the new value, but all
        subsequent actions in a job will have access. Environment variables are case-sensitive and you can include
        punctuation.
        """
        print(f"::set-env name={name}::{value}")

    @staticmethod
    def set_output(name: str, value: str):
        """
        Sets an action's output parameter.

        Optionally, you can also declare output parameters in an action's metadata file.
        """
        print(f"::set-output name={name}::{value}")

    @staticmethod
    def add_path(path: Path):
        """
        Prepends a directory to the system PATH variable for all subsequent actions in the current job.

        The currently running action cannot access the new path variable.
        """
        print(f"::add-path::{path}")

    @staticmethod
    def debug(message: str):
        """
        Prints a debug message to the log.

        You must create a secret named ACTIONS_STEP_DEBUG with the value true to see the debug messages set by this
        command in the log.
        """
        for line in message.splitlines():
            print(f"::debug::{line}")

    @staticmethod
    def warning(message: str, *, file: Optional[str] = None, line: int = 0, col: int = 0):
        """
        Creates a warning message and prints the message to the log.

        You can optionally provide a filename (file), line number (line), and column (col) number where the warning
        occurred.
        """
        if file:
            print(f"::warning file={file},line={line},col={col}::{newlines_to_spaces(message)}")
        else:
            for message_line in message.splitlines():
                print(f"::warning::{message_line}")

    @staticmethod
    def error(message: str, *, file: Optional[str] = None, line: int = 0, col: int = 0):
        """
        Creates an error message and prints the message to the log.

        You can optionally provide a filename (file), line number (line), and column (col) number where the warning
        occurred.
        """
        if file:
            print(f"::error file={file},line={line},col={col}::{newlines_to_spaces(message)}")
        else:
            for message_line in message.splitlines():
                print(f"::error::{message_line}")

    @staticmethod
    def add_mask(value: str):
        """
        Masking a value prevents a string or variable from being printed in the log.

        Each masked word separated by whitespace is replaced with the * character. You can use an environment variable
        or string for the mask's value.
        """
        print(f"::add-mask::{value}")

    @staticmethod
    def stop_commands(token: str = _DEFAULT_TOKEN):
        """
        Stops processing any workflow commands.

        This special command allows you to log anything without accidentally running a workflow command. For example,
        you could stop logging to output an entire script that has comments.
        """
        print(f"::stop-commands::{token}")

    @staticmethod
    def start_commands(token: str = _DEFAULT_TOKEN):
        """To start workflow commands, pass the token that you used to stop workflow commands."""
        print(f"::{token}::")

    def get_pull_request_api_from_event(self) -> Optional[github.pulls.PullRequest]:
        """
        Return a GitHub API client to manipulate the pull request that triggered this action.

        :raises ActionError: if the event is not a Pull Request
        """
        if self.github_env.event_name != EVENT_PULL_REQUEST:
            raise ActionError("Trying to get Pull Request data but event is not a Pull Request")

        owner = self.github_env.event_payload_find("repository/owner/login")
        repo_name = self.github_env.event_payload_find("repository/name")
        number = self.github_env.event_payload_find("pull_request/number")
        pull_request = self.github_api.pull_request(owner, repo_name, number)

        return pull_request

    def get_input(self, input_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Return the value of the action input with the given name, or if empty the given default value or None.
        :param input_name: name of the input in action metadata
        :param default: default value if input is empty
        :return: the value of the action input with the given name, or if empty the given default value or None
        """
        return self.github_env.get("INPUT_" + input_name.upper().replace(" ", "_"), default)

    @contextmanager
    def without_commands(self, token: Optional[str] = None):
        """
        Return a context that will disable all GitHub actions using given or default token.
        Once in this context any output can be sent to stdout without GitHub interpreting any commands in it.
        :param token: a unique random string that will mark start and end of logs without command interpretation
        :return: a non-re-entrant context manager
        """
        unique = token or random_str()
        try:
            self.stop_commands(unique)
            yield
        finally:
            self.start_commands(unique)


def newlines_to_spaces(text: str) -> str:
    """
    Remove all newlines from given text so it can be printed on a single line in action logs.

    :param text: a log text
    :return: the given text with all newlines replaced by simple spaces
    """
    return text.replace("\r", "").replace("\n", " ")


def random_str(length: int = 20) -> str:
    return "".join(secrets.choice(string.ascii_letters) for _ in range(length))


class ActionError(Exception):
    """Superclass of all exception raised by GitHub actions."""


def json_find(json_tree: Dict[str, Any], path: str, default: Optional[Any] = None) -> Optional[Any]:
    """
    Safely walk through a JSON tree to find a value in a map in a map in a map.

    some_json["pull_request"]["head"]["comment"] may raise KeyError if any piece of json is empty.
    json_find(some_json, "pull_request/head/comment") is safer; in case of missing data it simply returns None.
    """
    try:
        for path_part in path.split("/"):
            json_tree = json_tree[path_part]
        return json_tree or default
    except (KeyError, TypeError):
        return default
