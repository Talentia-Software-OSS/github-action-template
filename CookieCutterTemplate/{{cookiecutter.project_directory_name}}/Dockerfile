FROM python:3.8-slim-buster

ENV PYTHONPATH="/pythonpath"

COPY requirements.lock ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY {{cookiecutter.package_name}}/*.py /pythonpath/{{cookiecutter.package_name}}/

ENTRYPOINT ["action-entrypoint", "{{cookiecutter.package_name}}.action.{{cookiecutter.action_class_name}}"]
