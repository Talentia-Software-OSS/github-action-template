from unittest.mock import patch

from github_action_template.entrypoint import main
from github_action_template.framework import ActionError


@patch("github_action_template.entrypoint.sys")
@patch("github_action_template.entrypoint.os")
@patch("github_action_template.entrypoint.importlib")
@patch("github_action_template.entrypoint.GitHubEnvironment")
def test_main_should_call_action(mock_env, mock_importlib, mock_os, mock_sys):
    mock_os.environ = {"X": "Y", "Y": "Z"}
    mock_sys.argv = ["entrypoint.sh", "pkg.action.Class", "x", "y"]

    assert main() == 0

    mock_env.assert_called_with(mock_os.environ)
    mock_importlib.import_module.assert_called_with("pkg.action")
    mock_importlib.import_module.return_value.Class.assert_called_with(mock_env.return_value)
    mock_importlib.import_module.return_value.Class.return_value.run.assert_called_with(["x", "y"])


@patch("github_action_template.entrypoint.sys")
@patch("github_action_template.entrypoint.os")
@patch("github_action_template.entrypoint.importlib")
@patch("github_action_template.entrypoint.GitHubEnvironment")
def test_main_should_return_one_on_instantiate_failure(mock_env, mock_importlib, mock_os, mock_sys):
    mock_os.environ = {"X": "Y", "Y": "Z"}
    mock_importlib.import_module.return_value.Class.side_effect = TypeError("Problem")
    mock_sys.argv = ["entrypoint.sh", "pkg.action.Class", "x", "y"]

    assert main() == 1

    mock_env.assert_called_with(mock_os.environ)


@patch("github_action_template.entrypoint.sys")
@patch("github_action_template.entrypoint.os")
@patch("github_action_template.entrypoint.importlib")
@patch("github_action_template.entrypoint.GitHubEnvironment")
def test_main_should_return_two_on_failure(mock_env, mock_importlib, mock_os, mock_sys):
    mock_os.environ = {"X": "Y", "Y": "Z"}
    mock_importlib.import_module.return_value.Class.return_value.run.side_effect = ActionError("Failure")
    mock_sys.argv = ["entrypoint.sh", "pkg.action.Class", "x", "y"]

    assert main() == 2

    mock_env.assert_called_with(mock_os.environ)
    mock_importlib.import_module.return_value.Class.return_value.run.assert_called_with(["x", "y"])


@patch("github_action_template.entrypoint.sys")
@patch("github_action_template.entrypoint.os")
@patch("github_action_template.entrypoint.importlib")
@patch("github_action_template.entrypoint.GitHubEnvironment")
def test_main_should_return_two_on_runtime_error(mock_env, mock_importlib, mock_os, mock_sys):
    mock_os.environ = {"X": "Y", "Y": "Z"}
    mock_importlib.import_module.return_value.Class.return_value.run.side_effect = TypeError("Problem")
    mock_sys.argv = ["entrypoint.sh", "pkg.action.Class", "x", "y"]

    assert main() == 2

    mock_env.assert_called_with(mock_os.environ)
