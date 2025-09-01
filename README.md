# The FAIRagro Middleware #

This is a first implementation of the FAIRagro middleware. It scrapes schema.org meta data from the list of defined research repositories and writes them into a git repository. Also OpenTelemetry tracing can be configured.

## Usage ##

To use this script, you need to have a Python version 3.11 installed.

To setup your environment in Powershell (bash would be nearly identical):

```bash
cd <your local project directory>
python -m pip install --upgrade pip pipdeptree setuptools wheel
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Running the script is very simple:

```bash
cd middleware
python main.py -c ../config.yml [--no-git]
```

## Configuration ##

The script reads in a configuration file. This file can be specified via the command line script '-c', otherwise the file `config.yml` in the folder `middleware/utils` will be used. You can find the default config file with explaining comments next to this README file. The name is `config.yml`.

## Using Docker ##

There is a [Wolfi](https://github.com/wolfi-dev)-based `Dockerfile` to build a docker image:

```bash
docker build \
  -t middleware:test \
  --label org.opencontainers.image.source=https://github.com/fairagro/m4.2_basic_middleware \
  --label org.opencontainers.image.title=m4.2_basic_middleware .
```

Note: we set these two labels so the resulting image will pass our `container-structure-test`s (see below).

To run this image, please use this command:

```bash
SSH_PRIVATE_KEY="$(cat ./ssh_key.pem)"
docker run \
  --rm --user nonroot --cap-drop all \
  --tmpfs /tmp/ssh:rw,noexec,nosuid,size=64k \
  -e SSH_PRIVATE_KEY="$SSH_PRIVATE_KEY" \
  -v ./config.yml:/middleware/config.yml \
  middleware:test
```

Running the image from dockergub:

```bash
SSH_PRIVATE_KEY="$(cat ./ssh_key.pem)"
docker run \
  --rm --user nonroot --cap-drop all \
  --tmpfs /tmp/ssh:rw,noexec,nosuid,size=64k \
  -e SSH_PRIVATE_KEY="$SSH_PRIVATE_KEY" \
  -v ./config.yml:/middleware/config.yml \
  zalf/fairagro_basic_middleware:latest
```

A few notes on this docker run call:

- We run the container without root privileges as user `nonroot`. This user is defined in the Wolfi base image.
- `config.yml` and `ssh_key.pem` specify the configuration. `config.yml` is mounted as volume, whereas the content of `ssh_key.pem`
  is passed as environment variable `SSH_PRIVATE_KEY`. This is to prevent from permission issues. The ssh key is for git interaction with the
  remote repository specified in the config file. Of course the key already needs to be registered with the git repo.
- As an alternative to access git via `ssh`, it's also possible to use the `https` protocol. In this case you will need to create a
  personal access token in the github user interface to gain write access to the middleware repo. This access token is passed in terms of the environment variable `ACCESS_TOKEN`.

## Notes on the python version ##

Older python versions than 3.11 do not support the type hint `Annotated[Optional[...]]` which we make use of. Newer python versions do not include the
former standard library `imp` any more that is used by the required library `pyRfda3`. Unfortunately there is no maintainer for any more for `pyRfda3`.
While the `imp` import issue has been fixed in the git repo, that version is not available through `pip`. The correct way to deal with this would be,
either to take over maintainership of `pyRfda3` or to replace or contribute to the `extruct` library which makes use of `pyRfd3`.

## On the github pipeline ##

This repo makes use of github features to work as CI pipeline.

The main idea is: you cannot deploy to the main branch as it is protected by github. Instead you have to create a feature branch and create a pull request
for that branch when you are finished. Merging that pull request requires a code review within in github.

These github actions will come into play:

- `Python Code Check`: it will be triggered on every push. It will lint and unit test your code.

- `Docker Build`: it will also be triggered on every push to build a docker image. In case it's not a push to the `main` branch, that image will be thrown
  away immediately. So in this case this is merely a check if the image can be build successfully. The final push to `main`, resulting from a pull request,
  will upload the built image to dockerhub, though. The dockerhub credentials are stored as github secrets.

To download the resulting image from dockerhub:

```powershell
docker pull zalf/fairagro_basic_middleware
```

## Versioning ##

This repo uses [Semantic Versioning](https://semver.org/). Every commit to the main branch (aka the result of each pull request) will be tagged with a
version number of the form `v1.2.3`, where '1' is the major version, '2' the minor version and '3' the patch level.

The tool [`GitVersion`](https://gitversion.net/) is used to automatically create new versions. It is triggered by the `Docker Build` workflow that also
actually creates the git tags. To define how to increase the version, `GitVersion` is configured to interpret
[Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/). So you are expected to write commit messages that conform to this spec.

A conventional commit message looks like this:

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Allowed types are: 'build', 'chore', 'ci', 'docs', 'feat', 'fix', 'style', 'refactor', 'perf' and 'test'.
Each type denotes a corresponding change. All types except 'feat' (for feature) will induce an increase of the patch level, whereas 'feat' will increase
the minor version.

To increase the major version, you have to add a '!' to the type or add this to the footer:

```text
BREAKING CHANGE: <description>
```

The scope denotes the part of your project you're working on -- e.g 'frontend', 'backend', 'parser', etc. Currently there are no defined scopes
for this repo.

## About Testing ##

This repository currently has two distinct sets of automated tests:

- [Python unittests](https://docs.python.org/3/library/unittest.html). Python packages in the source tree are expected to define a `test` directory that contains the
  corresponding unit test. Note that not every package current implement unit tests. To run the unit tests you can use this command:

  ```powershell
  python -m unittest discover -s middleware
  ```

  Unit tests are executed automatically by the github action `Python Code Check`

- [Container structure tests](https://github.com/GoogleContainerTools/container-structure-test). These tests are used to check if ready built docker containers
  work as expected. You can find everything related to these tests in the folder `test/container-structure-test`. This folder includes a special middleware config
  that is used for testing, without accessing real research repositories. You will also find the actual `container-structure-test` config that defines the actual tests
  as well as two mock files that define a sitemap file and a dataset web page to be used by the tests.

  To run the test setup (whithout actual testing):

  ```powershell
  python middleware\main.py `
    -c test\container-structure-test\image_test_config.yml `
    --no-git
  ```

  using a docker container instead:

  ```powershell
  docker run `
    --user nonroot --rm --cap-drop all`
    middleware:test `
    python main.py -c test/container-structure-test/image_test_config.yml --no-git
  ```

  Note: we've copied the `test/container-structure-test` folder into the image, using the docker file. Alternatively the folder can be mounted into the image, but
  this makes things complicated when using `container-structure-test`. This clutters the image with some unnessary files in production, but as far as I can tell, they
  are not harmful.

  To run the `container-structure-test` itself:

  ```powershell
  container-structure-test test `
    --image middleware:test `
    --config .\test\container-structure-test\container-structure-test-config.yml
  ```

  Container structure tests are executed automatically the github action `Docker Build`.
  