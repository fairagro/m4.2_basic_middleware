# The FAIRagro Middleware #

This is a first implementation of the FAIRagro middleware. It scrapes schema.org meta data from the list of defined research repositories and writes them into a git repository. Also OpenTelemetry tracing can be configured.

## Usage ##

To use this script, you need to have a Python version 3.11 installed.

To setup your environment in Powershell (bash would be nearly identical):

```powershell
cd <your local project directory>
python -m pip install --upgrade pip pipdeptree setuptools wheel
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Running the script is very simple:

```powershell
python src\main.py -c ..\config.yml [--no-git]
```

## Configuration ##

The script reads in a configuration file. This file can be specified via the command line script '-c', otherwise the file 'config.yml' next to the script file will be used. You can find the default config file with explaining comments next to this README file. The name is 'config.yml'

## Using Docker ##

There is a Wolfi-based `Dockerfile` to build a docker image:

```powershell
docker build -t middleware:test .
```

To run this image, please use this command:

```powershell
docker run --user 65532 -v .\config.yml:/middleware/utils/config.yml -v .\ssh_key.pem:/middleware/ssh_key.pem --rm middleware:test
```

A few notes on this docker run call:

- We run the container without root privileges a user `nonroot`. This user is defined the Wolfi base image.
- `config.yml` and `ssh_key.pem` specify the configuration and are mounted into the container.
- The local git working folder would preferably also be mounted into the container so its contents could be cached between container runs. But this seems not be possible -- at least not without administrational permission on the host machine. The issue is that mounted volumes always belong to root, but the container does not run with root permissions, so it has to write access to the folder.

## Notes on the python version ##

Older python versions than 3.11 do not support the type hint `Annotated[Optional[...]]` which we make use of. Newer python versions do not include the former standard library `imp` any more that is used by the required library `pyRfda3`. Unfortunately there is no maintainer for any more for `pyRfda3`. While the `imp` import issue has been fixed in the git repo, that version is not available through `pip`. The correct way to deal with this would be, either to take over maintainership of `pyRfda3` or to replace or contribute to the `extruct` library which makes use of `pyRfd3`.

## On the github "pipeline" ##

This repo makes use of github features to work as CI pipeline.

The main idea is: you cannot deploy to the main branch as it is protected by github. Instead you have to create a feature branch and create a pull request
for that branch when you are finished. Merging that pull request requires a code review within in github.

There are also github actions that perform typical CI tasks:

- `Python Code Check`: it will be triggered on every push. It will lint and unit test your code.

- `Docker Build`: it will also be triggered on every push to build a docker image. In case it's not a push to the `main` branch, that image will be thrown
  away immediately. So in this case this is merely a check if the image can be build successfully. The final push to `main`, resulting from a pull request
  will upload the build image to dockerhub, though. The dockerhub credentials are stored as github secrets.
