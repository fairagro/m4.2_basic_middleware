# The FAIRagro Middleware #

This is a first implementation of the FAIRagro middleware. It scrapes schema.org meta data from the list of defined research repositories and writes them into a git repository. Also OpenTelemetry tracing can be configured.

## Usage ##

To use this script, you need to have a Python version 3.11 installed (we're using the type hint `Annotated[Optional[...]]` which only works as expcted with Python 3.11)

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
