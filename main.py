import yaml
import itertools
import extruct
import requests
import opentelemetry.instrumentation.requests
from w3lib.html import get_base_url
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import json
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.semconv.trace import SpanAttributes


# Initialize OpenTelemetry for Tracing to Console
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(ConsoleSpanExporter())
)
otel_tracer = trace.get_tracer("FAIRagro.middleware.tracer")
opentelemetry.instrumentation.requests.RequestsInstrumentor().instrument()


def get_sitemaps_from_config(config_file):
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
        return config['sitemaps']

def get_url(url):
    r = requests.get(url)
    # e!DAL returns the HTTP content-type 'text/html' which implies ISO-8859-1 encoding.
    # Nevertheless UTF-8 encoding is used. This confuses the requests library.
    # Fortunately the requests library can detect the encoding automatically. But we need to
    # apply it explicitly.
    # The correct content-type for e!DAL would be 'text/html; charset=utf-8'.
    content = r.content.decode(r.apparent_encoding)
    return content

def extract_sites(sitemap_url):
    sitemap_xml = get_url(sitemap_url)
    xml_root = ET.fromstring(sitemap_xml)
    sites = [ url.text for url in xml_root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc' )]
    return sites

def extract_jsonld(html):
    soup = BeautifulSoup(html, 'html.parser')
    json_ld = soup.find_all('script', type='application/ld+json')
    result = [ js.text for js in json_ld ]
    return result
    
def extract_schema_org_jsonld(html, url):
    base_url = get_base_url(html, url)

    # only scrape JSON-LD data.
    # e!DAL also offers DublinCore and RDFa, but this does not add useful information.
    # (RDFa is not related to metadata at all, probably it's added by the HTML renderer.
    # DublinCore just reflects the JSON-LD data, but has less capabilities.)
    metadata = extruct.extract(html, 
                               base_url=base_url,
                               uniform=True,
                               syntaxes=['json-ld'])
    return metadata['json-ld']

@otel_tracer.start_as_current_span("extract_schema_org_or_issue_error")
def extract_schema_org_or_log_error(url):
    otel_span = trace.get_current_span()
    otel_span.set_attribute(SpanAttributes.URL_FULL, url)
    try:
        content = get_url(url)
        metadata = extract_schema_org_jsonld(content, url)
        return metadata
    except Exception as e:
        suspicious_jsonld = ''.join(extract_jsonld(content))
        otel_span.set_attribute("FAIRagro.middleware.suspicious_jsonld", suspicious_jsonld)
        otel_span.record_exception(e)
        otel_span.add_event("Could not extract schema.org meta data in JSON-LD format")
        return None
 
def extract_many_schema_org(urls):
    for url in urls:
        metadata = extract_schema_org_or_log_error(url)
        # metadata might be None, if schema.org parser failed.
        if metadata:
            # Note: if metadata is not None, it's a list that may contain several JSON-LD entries.
            # e!DAL sometimes defines two entries: "@type":"Dataset" and "@type":"Taxon".
            yield metadata

def scrape_repo(name, sitemap_url):
    sites = extract_sites(sitemap_url)
    count_sites = len(sites)
    metadata = list(extract_many_schema_org(sites))
    count_metadata = len(metadata)
    result = list(itertools.chain.from_iterable(metadata))
    with open(f'{name}.json', 'w') as f:
        f.write(json.dumps(result, indent=2))

@otel_tracer.start_as_current_span("main")   
def main():
    try:
        sitemaps = get_sitemaps_from_config('config.yml')
        for sitemap in sitemaps:
            scrape_repo(sitemap['name'], sitemap['url'])
    except Exception as e:
        otel_span = trace.get_current_span()
        otel_span.record_exception(e)
        otel_span.set_status(Status(StatusCode.ERROR))
        
if __name__ == '__main__':
    main()



# sites = [
#     # "https://maps.bonares.de/finder/resources/googleds/datasets/fca18db3-fc1b-4c1c-bb81-afc0dcadc29e.html"
#     "https://doi.org/10.5447/ipk/2012/10"
# ]