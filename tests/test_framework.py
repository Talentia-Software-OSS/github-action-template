import json
import string
from pathlib import Path
from typing import Dict, Tuple, Union
from unittest.mock import MagicMock, call, patch

import pytest

from github_action_template.framework import (ActionError, GitHubAction, GitHubEnvironment, _DEFAULT_TOKEN, json_find,
                                              newlines_to_spaces, random_str, )


@pytest.fixture
def event_json_file(tmp_path):
    data = {"key": {"subkey": "value"}}
    event_json_dir = tmp_path / "sub"
    event_json_dir.mkdir()
    event_json_file = event_json_dir / "event.json"
    with event_json_file.open("w") as output_to_file:
        json.dump(data, output_to_file)
    yield event_json_file
    event_json_file.unlink()
    event_json_dir.rmdir()


@patch("github_action_template.framework.GitHub")
def test_github_action_api(mock_github):
    github_env = MagicMock(spec=GitHubEnvironment)
    github_env.secret_token = "hush"

    action = GitHubAction(github_env)
    assert action.github_api == mock_github.return_value
    mock_github.assert_called_with(token=github_env.secret_token)


@pytest.mark.parametrize("command, args, kwargs, printed", [
    ("set_env", ("XXX", "YYY"), {}, "::set-env name=XXX::YYY"),
    ("set_output", ("XXX", "YYY"), {}, "::set-output name=XXX::YYY"),
    ("add_path", ("XXX",), {}, "::add-path::XXX"),
    ("debug", ("XXX",), {}, "::debug::XXX"),
    ("warning", ("XXX",), {}, "::warning::XXX"),
    ("warning", ("XXX",), {"file": "FILE"}, "::warning file=FILE,line=0,col=0::XXX"),
    ("warning", ("XXX",), {"file": "FILE", "line": 3, "col": 4}, "::warning file=FILE,line=3,col=4::XXX"),
    ("error", ("XXX",), {}, "::error::XXX"),
    ("error", ("XXX",), {"file": "FILE"}, "::error file=FILE,line=0,col=0::XXX"),
    ("error", ("XXX",), {"file": "FILE", "line": 3, "col": 4}, "::error file=FILE,line=3,col=4::XXX"),
    ("add_mask", ("XXX",), {}, "::add-mask::XXX"),
    ("stop_commands", ("XXX",), {}, "::stop-commands::XXX"),
    ("stop_commands", tuple(), {}, f"::stop-commands::{_DEFAULT_TOKEN}"),
    ("start_commands", ("XXX",), {}, "::XXX::"),
    ("start_commands", tuple(), {}, f"::{_DEFAULT_TOKEN}::"),
    ])
def test_github_action_command(command: str, args: Tuple[str], kwargs: Dict[str, Union[str, int]], printed: str):
    with patch("github_action_template.framework.print") as mock_print:
        github_env = MagicMock(spec=GitHubEnvironment)
        action = GitHubAction(github_env)
        callable_command = getattr(action, command)
        callable_command(*args, **kwargs)
        mock_print.assert_called_with(printed)


@pytest.mark.parametrize("command, kwargs, printed", [
    ("debug", {}, (call("::debug::XXX"), call("::debug::YYY"), call("::debug::ZZZ"))),
    ("warning", {}, (call("::warning::XXX"), call("::warning::YYY"), call("::warning::ZZZ"))),
    ("warning", {"file": "FILE"}, (call("::warning file=FILE,line=0,col=0::XXX YYY ZZZ"),)),
    ("warning", {"file": "FILE", "line": 3, "col": 4}, (call("::warning file=FILE,line=3,col=4::XXX YYY ZZZ"),)),
    ("error", {}, (call("::error::XXX"), call("::error::YYY"), call("::error::ZZZ"))),
    ("error", {"file": "FILE"}, (call("::error file=FILE,line=0,col=0::XXX YYY ZZZ"),)),
    ("error", {"file": "FILE", "line": 3, "col": 4}, (call("::error file=FILE,line=3,col=4::XXX YYY ZZZ"),)),
    ])
def test_github_action_command_with_newline(command: str, kwargs: Dict[str, Union[str, int]], printed: str):
    with patch("github_action_template.framework.print") as mock_print:
        github_env = MagicMock(spec=GitHubEnvironment)
        action = GitHubAction(github_env)
        callable_command = getattr(action, command)
        callable_command("XXX\nYYY\nZZZ", **kwargs)
        mock_print.assert_has_calls(printed)


def test_github_action_get_pull_request_api_from_event_not_a_pr():
    github_env = MagicMock(spec=GitHubEnvironment)
    action = GitHubAction(github_env)
    with pytest.raises(ActionError):
        action.get_pull_request_api_from_event()


@patch("github_action_template.framework.GitHub")
def test_github_action_get_pull_request_api_from_event(mock_github):
    github_env = GitHubEnvironment({"GITHUB_EVENT_NAME": "pull_request", "GITHUB_TOKEN": "TOKEN"})
    github_env._cached_json_payload = {
        "repository": {"owner": {"login": "alogin"},
                       "name": "repo_name"
                       },
        "pull_request": {"number": "1",
                         "body": "body"
                         }
        }
    action = GitHubAction(github_env)
    assert action.get_pull_request_api_from_event() is mock_github.return_value.pull_request.return_value
    mock_github.assert_called_with(token="TOKEN")
    mock_github.return_value.pull_request.assert_called_with("alogin", "repo_name", "1")


def test_github_action_init():
    github_env = MagicMock(spec=GitHubEnvironment)
    action = GitHubAction(github_env)
    assert action.github_env == github_env


def test_github_environment_actions():
    assert GitHubEnvironment({"GITHUB_ACTIONS": "True"}).actions
    assert not GitHubEnvironment({"GITHUB_ACTIONS": "False"}).actions
    assert not GitHubEnvironment({"GITHUB_ACTIONS": "SPAM"}).actions
    assert not GitHubEnvironment({}).actions


def test_github_environment_event_path():
    assert GitHubEnvironment({"GITHUB_EVENT_PATH": "/somewhere/event.json"}).event_path == Path("/somewhere/event.json")
    assert GitHubEnvironment({}).event_path == Path("event.json")


def test_github_environment_event_payload(event_json_file: Path):
    github_env = GitHubEnvironment({"GITHUB_EVENT_PATH": str(event_json_file)})
    assert github_env.event_payload == {"key": {"subkey": "value"}}


def test_github_environment_event_payload_find(event_json_file: Path):
    github_env = GitHubEnvironment({"GITHUB_EVENT_PATH": str(event_json_file)})
    assert github_env.event_payload_find("key/subkey") == "value"
    assert github_env.event_payload_find("key/notthere", "default") == "default"


def test_github_environment_event_payload_may_raise(event_json_file: Path):
    event_json_file.write_text("THIS IS NOT A VALID JSON")
    github_env = GitHubEnvironment({"GITHUB_EVENT_PATH": str(event_json_file)})
    with pytest.raises(ActionError):
        assert github_env.event_payload is None


@pytest.mark.parametrize("key, attr", [
    ("GITHUB_WORKFLOW", "workflow"),
    ("GITHUB_RUN_ID", "run_id"),
    ("GITHUB_ACTION", "action"),
    ("GITHUB_ACTOR", "actor"),
    ("GITHUB_REPOSITORY", "repository"),
    ("GITHUB_EVENT_NAME", "event_name"),
    ("GITHUB_SERVER_URL", "server_url"),
    ("GITHUB_API_URL", "api_url"),
    ("GITHUB_GRAPHQL_URL", "graphql_url"),
    ("GITHUB_TOKEN", "secret_token")
    ])
def test_github_environment_mandatory_strs(key, attr):
    assert getattr(GitHubEnvironment({key: "xxx"}), attr) == "xxx"
    with pytest.raises(ActionError):
        getattr(GitHubEnvironment({}), attr)


@pytest.mark.parametrize("key, attr", [
    ("GITHUB_SHA", "sha"),
    ("GITHUB_REF", "ref"),
    ("GITHUB_HEAD_REF", "head_ref"),
    ("GITHUB_BASE_REF", "base_ref")
    ])
def test_github_environment_optional_strs(key, attr):
    assert getattr(GitHubEnvironment({key: "xxx"}), attr) == "xxx"
    assert getattr(GitHubEnvironment({}), attr) is None


@pytest.mark.parametrize("key, attr, default", [
    ("HOME", "home", "."),
    ("GITHUB_EVENT_PATH", "event_path", "event.json"),
    ("GITHUB_WORKSPACE", "workspace", "."),
    ])
def test_github_environment_path_has_default(key, attr, default):
    # Cannot mix regular fixtures like tmpdir and mark.parametrize :(
    assert getattr(GitHubEnvironment({key: "/somewhere"}), attr) == Path("/somewhere")
    assert getattr(GitHubEnvironment({}), attr) == Path(default)


def test_github_environment_run_number():
    assert GitHubEnvironment({"GITHUB_RUN_NUMBER": "15"}).run_number == 15
    assert GitHubEnvironment({}).run_number == 1
    with pytest.raises(ActionError):
        assert not GitHubEnvironment({"GITHUB_RUN_NUMBER": "SPAM"}).run_number


def test_json_find():
    data = {"color": "blue",
            "empty": None,
            "team": {"goal": "john", "attacker": "bob"},
            "list": ["sugar", "coffee", "cigarettes"],
            }
    assert json_find(data, "color") == "blue"
    assert not json_find(data, "color/shade")
    assert not json_find(data, "colour")
    assert json_find(data, "colour", "default") == "default"
    assert not json_find(data, "colour/shade")
    assert json_find(data, "colour/shade", "default") == "default"
    assert not json_find(data, "empty")
    assert json_find(data, "empty", "default") == "default"
    assert not json_find(data, "empty/void")
    assert json_find(data, "empty/void", "default") == "default"
    assert json_find(data, "team/goal") == "john"
    assert not json_find(data, "team/goal/age")
    assert json_find(data, "list") == ["sugar", "coffee", "cigarettes"]


def test_newlines_to_spaces():
    assert newlines_to_spaces("") == ""
    assert newlines_to_spaces("SOme text") == "SOme text"
    assert newlines_to_spaces("SOme\ntext") == "SOme text"
    assert newlines_to_spaces("SOme\r\nlong\r\ntext") == "SOme long text"


@patch("github_action_template.framework.secrets.choice")
def test_random_str(mock_choice):
    mock_choice.side_effect = list(string.ascii_lowercase)
    assert random_str() == "abcdefghijklmnopqrst"
    assert random_str(5) == "uvwxy"
