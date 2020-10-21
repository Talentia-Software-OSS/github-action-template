from unittest.mock import MagicMock, call, patch

from {{cookiecutter.package_name}}.action import {{cookiecutter.action_class_name}}
from github_action_template.framework import GitHubEnvironment


@patch("github_action_template.framework.GitHub")
def test_action_simple(mock_github):
    github_env = MagicMock(spec=GitHubEnvironment)

    action = {{cookiecutter.action_class_name}}(github_env)
    action.run(["arg1", "arg2"])

    mock_github.assert_not_called()


@patch("github_action_template.framework.GitHub")
def test_action_pull_request(mock_github):
    github_env = MagicMock(spec=GitHubEnvironment)
    github_env.event_name = "pull_request"
    github_env.event_payload_find.side_effect = ["owner", "repo_name", "number"]

    action = {{cookiecutter.action_class_name}}(github_env)
    action.run(["arg1", "arg2"])

    mock_github.assert_called_once()
    github_env.event_payload_find.assert_has_calls([
        call("repository/owner/login"),
        call("repository/name"),
        call("pull_request/number"),
        ])
    mock_github.return_value.pull_request.assert_called_with("owner", "repo_name", "number")
