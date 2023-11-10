# The FAIRagro Middleware #

This is a first very quick implementation of the FAIRagro middleware. It currently scrapes the e!DAL meta data offered in schema.org JSON-LD format. It starts scraping from the e!DAL sitemap `https://doi.ipk-gatersleben.de/sitemap.xml`. The result is a single JSON-LD file containing all meta data in a single array. It's written to stdout.

## Usage ##

To use this script, you need to have a current Python version installed (at least Python major version 3, of course -- the mininal minor version is unknown).

To setup your environment in Powershell (bash would be nearly identical):

```powershell
cd <your local project directory>
python -m pip install --upgrade pip setuptools wheel
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Running the script is very simple:
```powershell
python .\main.py
```