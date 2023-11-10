import sys
import extruct
import requests
import pprint
from w3lib.html import get_base_url
import xml.etree.ElementTree as ET

sitemap_url = 'https://doi.ipk-gatersleben.de/sitemap.xml'


def extract_sites(sitemap_url):
    # Fetch the XML data
    response = requests.get(sitemap_url)
    sitemap_xml = response.text

    # Parse the XML data
    root = ET.fromstring(sitemap_xml)
    sites = [ url.text for url in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc' )]

    return sites

def extract_metadata(url):
    r = requests.get(url)
    base_url = get_base_url(r.text, r.url)
    metadata = extruct.extract(r.text, 
                               base_url=base_url,
                               uniform=True)
    return metadata


def main():
    stdout = pprint.PrettyPrinter(indent=2, stream=sys.stdout)
    stderr = pprint.PrettyPrinter(indent=2, stream=sys.stderr)

    sites = extract_sites(sitemap_url)

    # Extract metadata
    result = []
    for site in sites:
        try:
            metadata = extract_metadata(site)
            result += metadata['json-ld']
        except Exception as e:
            stderr.pprint(e)

    stdout.pprint(result)


if __name__ == '__main__':
    main()