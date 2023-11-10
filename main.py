import sys
import extruct
import requests
import pprint
from w3lib.html import get_base_url
import xml.etree.ElementTree as ET
# from bs4 import BeautifulSoup
# import json

sitemap_url = 'https://doi.ipk-gatersleben.de/sitemap.xml'


# # Define a function to filter out JSON-LD script elements
# def filter_elements(tag):
#     if tag.name == 'script' and tag.get('type') == 'application/ld+json':
#         return True
#     return False

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
    # e!DAL returns the HTML content-type 'text/html' which implies ISO-8859-1 encoding.
    # Nevertheless UTF-8 encoding is used. This confuses the requests library.
    # Fortunately the requests library can detect the encoding automatically. But we need to
    # apply it explicitly.
    # The correct content-type would be 'text/html; charset=utf-8'.
    html = r.content.decode(r.apparent_encoding)
    base_url = get_base_url(html, r.url)
    
    # soup = BeautifulSoup(r.content.decode(r.apparent_encoding), 'html.parser')
    # json_ld = filter(filter_elements, soup.find_all())
    # for j in json_ld:
    #     t = j.text
    #     js = json.loads(t, strict = False)

    # only scrape JSON-LD data.
    # e!DAL also offers DublinCore and RDFa, but this does not add useful information.
    # (RDFa is not related to metadata at all, probably it's added by the HTML renderer.
    # DublinCore just reflects the JSON-LD data, but has less capabilities.)
    metadata = extruct.extract(html, 
                               base_url=base_url,
                               uniform=True,
                               syntaxes=['json-ld'])
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
            stderr.pprint(site + ': ' + str(e))

    stdout.pprint(result)


if __name__ == '__main__':
    main()