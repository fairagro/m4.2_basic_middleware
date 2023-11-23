# The FAIRagro Middleware #

This is a first implementation of the FAIRagro middleware. It scrapes schema.org meta data from the list of defined research repositories and writes them into a git repository. The current version also outputs OpenTelemetry tracing information to stdout, so don't get confused about it. This needs to be changed before productive use.

## Usage ##

To use this script, you need to have a current Python version installed (at least Python major version 3, of course -- the mininal minor version is unknown).

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
python .\main.py [-c <config>]
```

## Configuration ##

The script reads in a configuration file. This file can be specified via the command line script '-c', otherwise the file 'config.yml' next to the script file will be used. This is the default config file -- which is hopefully self-explaining:

```yaml
sitemaps:
  - name: bonares
    url: https://maps.bonares.de/finder/resources/googleds/sitemap.xml
  - name: edal
    url: https://doi.ipk-gatersleben.de/sitemap.xml

# Note on paths: relative paths refer to the directory the middleware script resides in.
# You can omit the ssh_key_path if you have a local git setup with your personal key.
# If branch is omitted, the main branch is used
git:
  repo_url: git@github.com:fairagro/middleware_repo.git
  branch: main
  ssh_key_path: ssh_key.pem
  local_path: output
  user_name: "FAIRagro middleware"
  user_email: "middleware@fairagro.net"
```
