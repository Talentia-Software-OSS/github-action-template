# GitHub Action template

This project helps to create [custom GitHub actions](https://docs.github.com/en/free-pro-team@latest/actions/creating-actions)
with Python 3.

* GitHub: [Talentia-Software-OSS/github-action-python-template](https://github.com/Talentia-Software-OSS/github-action-python-template)
* Free and open source software: [BSD license](https://github.com/Talentia-Software-OSS/github-action-python-template/blob/master/LICENSE)

## Features

There are two ways to create a custom action: either by using JavaScript or
by [providing a Docker container](https://docs.github.com/en/free-pro-team@latest/actions/creating-actions/creating-a-docker-container-action)
that allows to use just any language.

This project helps to code a Python 3.8+ custom action, by providing:

- a [cookiecutter](https://github.com/cookiecutter/cookiecutter) template to generate a boilerplate project including
  Dockerfile, sample action code and metadata
- a Python package (this package) to serve as a lightweight framework for actions, used by our cookiecutter-generated 
  action
