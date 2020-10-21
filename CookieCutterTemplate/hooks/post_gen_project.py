#!/usr/bin/env python
import os
import platform
import subprocess
import sys

PROJECT_DIRECTORY = os.path.realpath(os.path.curdir)


def remove_file(filepath):
    os.remove(os.path.join(PROJECT_DIRECTORY, filepath))


def venv_path(*paths):
    if platform.system() == "Windows":
        return os.path.join(PROJECT_DIRECTORY, "{{ cookiecutter.optional_venv_dir_name }}", "Scripts", *paths)
    return os.path.join(PROJECT_DIRECTORY, "{{ cookiecutter.optional_venv_dir_name }}", "bin", *paths)


def virtualenv_vars():
    env_with_venv = os.environ.copy()
    env_with_venv["PYTHONHOME"] = ""
    env_with_venv["PATH"] = venv_path() + ":" + env_with_venv.get("PATH", "")
    env_with_venv["VIRTUAL_ENV"] = os.path.join(PROJECT_DIRECTORY, "{{ cookiecutter.optional_venv_dir_name }}")
    return env_with_venv


if __name__ == "__main__":
    # Remove files
    if not "{{ cookiecutter.optional_sonar_projectKey }}":
        remove_file("sonar-project.properties")

    # Create virtualenv
    if "create" in "{{ cookiecutter.virtualenv }}" and "{{ cookiecutter.optional_python_location_to_create_venv }}":
        print("Creating venv...")
        try:
            completed = subprocess.run([
                "{{ cookiecutter.optional_python_location_to_create_venv }}",
                "-m", "venv",
                "--clear",
                "{{ cookiecutter.optional_venv_dir_name }}"
                ],
                cwd=PROJECT_DIRECTORY)
            if completed.returncode:
                print("ERROR: venv command failed; aborting.")
                sys.exit(1)
        except FileNotFoundError:
            print("ERROR: Cannot run venv with {{cookiecutter.optional_python_location_to_create_venv}}.")
            sys.exit(1)

        subprocess.run([venv_path("python"), "-m", "pip", "install", "--upgrade", "pip", ],
                       cwd=PROJECT_DIRECTORY,
                       env=virtualenv_vars()
                       )

        print("Installing requirements...")
        completed = subprocess.run([
            venv_path("pip"), "install",
            "-r", "requirements.txt",
            "-r", "requirements-dev.txt"
            ],
            cwd=PROJECT_DIRECTORY,
            env=virtualenv_vars()
            )
        if completed.returncode:
            print("ERROR: virtualenv command failed; aborting.")
            sys.exit(1)

        subprocess.run([venv_path("pip"), "freeze", "pip", ">", os.path.join(PROJECT_DIRECTORY, "requirements.lock")],
                       cwd=PROJECT_DIRECTORY,
                       env=virtualenv_vars(),
                       shell=True
                       )
