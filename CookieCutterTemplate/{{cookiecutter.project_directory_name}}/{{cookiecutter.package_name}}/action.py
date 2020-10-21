"""A sample action skeleton to demonstrate framework use."""
from datetime import datetime
from pprint import pformat
from typing import List

from github_action_template.framework import EVENT_PULL_REQUEST, GitHubAction


class {{cookiecutter.action_class_name}}(GitHubAction):
    """This sample action simply logs action details."""

    def run(self, args: List[str]) -> None:
        """Perform the action."""

        with self.without_commands():
            print(f"Hello, {self.get_input('who-to-greet')}!")
            now = datetime.now().isoformat()
            print(f"It is now {now}.")
            print("------------------------------------------------------------")
        self.set_output("time", now)

        # Hello world! done. Additional sample actions below are not part of hello world!

        with self.without_commands():
            print(f"I am {self.github_env.action} started by {self.github_env.actor}.")
            print(f"I was run with args: {pformat(args)} and here is my payload:\n" +
                  pformat(self.github_env.event_payload))

            if self.github_env.event_name == EVENT_PULL_REQUEST:
                owner = self.github_env.event_payload_find("repository/owner/login")
                repo_name = self.github_env.event_payload_find("repository/name")
                number = self.github_env.event_payload_find("pull_request/number")

                pull_request = self.github_api.pull_request(owner, repo_name, number)
                print(f"Pull request was {pull_request}:\n{pformat(pull_request.__dict__)}")
