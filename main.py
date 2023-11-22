import os
from pathlib import Path, PurePosixPath
import datetime, pytz
import argparse, pathlib
import yaml
import itertools
import extruct
import requests
import git
from w3lib.html import get_base_url
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import json
from opentelemetry import trace #, metrics
from opentelemetry.trace import Status, StatusCode
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.sampling import ALWAYS_ON
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
# from opentelemetry.sdk.metrics import MeterProvider
# from opentelemetry.sdk.metrics.export import (
#     ConsoleMetricExporter,
#     PeriodicExportingMetricReader,
# )
from opentelemetry.semconv.trace import SpanAttributes
import opentelemetry.instrumentation.requests
import opentelemetry.instrumentation.urllib

# Initialize OpenTelemetry for Tracing to Console
# Note: it would be nice to read in the configuration from a file. But this is not supported yet.
# There is the possibility to define the configuration in terms of env variables, but the documentation
# is far from optimal and there seems to be no way set a console exporter.
trace.set_tracer_provider(
    TracerProvider(
        resource=Resource.create({
            "service.name": "FAIRagro middleware"
        }),
        sampler=ALWAYS_ON
    )
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(ConsoleSpanExporter())
)
opentelemetry.instrumentation.requests.RequestsInstrumentor().instrument()
opentelemetry.instrumentation.urllib.URLLibInstrumentor().instrument()
otel_tracer = trace.get_tracer("FAIRagro.middleware.tracer")

# Note: we would like to create a synchronous gauge to report the number of datasets within each repo.
# Unfortunately the OpenTelemetry Python SDK does not support this yet. We could try to work around with
# an observable gauge, but this is far from ideal.
#
# Initialize OpenTelemetry for Metrics to Console
# metrics.set_meter_provider(
#     MeterProvider(metrics_readers=[PeriodicExportingMetricReader(ConsoleMetricExporter())])
# )
# otel_meter = metrics.get_meter("FAIRagro.middleware.meter")


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

@otel_tracer.start_as_current_span("scrape_repo")
def scrape_repo_and_commit_to_git(name, sitemap_url, git_repo):
    otel_span = trace.get_current_span()
    otel_span.set_attribute("FAIRagro.middleware.repository_name", name)
    otel_span.set_attribute("FAIRagro.middleware.repository_sitemap_url", sitemap_url)
    start_timestamp = datetime.datetime.now(pytz.UTC)
    sites = extract_sites(sitemap_url)
    metadata = list(extract_many_schema_org(sites))
    # We should collect some metrics data, but OpenTelemetry does not yet support transmitting
    # simple synchronous gauge values.
    # count_sites = len(sites)
    # count_metadata = len(metadata)
    result = list(itertools.chain.from_iterable(metadata))
    path = os.path.join(git_repo.working_dir, f'{name}.json')
    with open(path, 'w') as f:
        f.write(json.dumps(result, indent=2))
    git_repo.index.add([path])
    formatted_time = start_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f %Z%z')
    git_repo.index.commit(
        f"FAIRagro middleware scraper for repo '{name}' with sitemap {sitemap_url}, started at {formatted_time}")

def make_ssh_key_path(original_path):
    # This is some ugly workaround for git on Windows. In this case git is based on MSYS, so the
    # ssh command requires POSIX compatible paths, whereas otherwise we deal with Windows paths
    # on Windows. Thus we need to convert the Windows path to the ssh key to MSYS-POSIX.
    # Be aware: this is brittle as it assumes that we always use MSYS ssh on Windows. Maybe there
    # are other ways to setup git.
    path = Path(original_path)
    parts = path.parts
    if parts[0].endswith(':\\'):
        parts = ['/', parts[0].rstrip(':\\'), *parts[1:]]
    return PurePosixPath(*parts)

def setup_git_repo(repo_info):
    script_dir = os.path.dirname(os.path.realpath(__file__))

    # find out a local path for the repo
    local_path = repo_info['local_path']
    if not os.path.isabs(local_path):
        local_path = os.path.normpath(os.path.join(script_dir, local_path))

    # find the ssh key and use it
    ssh_key_path = repo_info.get('ssh_key_path')
    if ssh_key_path and not os.path.isabs(ssh_key_path):
        ssh_key_path = os.path.normpath(os.path.join(script_dir, ssh_key_path))
        # Note: actutally /dev/null is OS-dependent. There is os.devnull to cope with this.
        # But for my git setup on Windwos, /dev/null is the correct value -- probably because
        # it uses an MSYS-based ssh. 
        os.environ['GIT_SSH_COMMAND'] = f'ssh -F /dev/null -i {make_ssh_key_path(ssh_key_path)}'

    # Initialize existing repo or clone it, if this hasn't been done yet
    try:
        repo_url = repo_info['repo_url']
        repo = git.Repo(local_path)
        if repo.remotes.origin.url != repo_url:
            raise RuntimeError(f"Repository {local_path} already exists and is not a clone of {repo_url}")
    except (git.exc.NoSuchPathError, git.exc.InvalidGitRepositoryError):
        repo = git.Repo.clone_from(repo_url, local_path)

    # set git config
    config_writer = repo.config_writer()
    config_writer.set_value("user", "name", repo_info['user_name'])
    config_writer.set_value("user", "email", repo_info['user_email'])
    config_writer.release()

    # switch into desired branch or create it
    branch = repo_info.get('branch', 'main')
    if branch not in repo.branches:
        # before we can create a branch we need have a commit, so try to access it
        try:
            _ = repo.head.commit
        except ValueError:
            # create initial commit
            readme = """# Purpose of this repository #

This repository is automatically maintained by the FAIRagro middleware. It stores scraped meta data from resarch data repositories in consolidated JSON-LD files.
"""
            readme_path = os.path.join(local_path, 'README.md')
            with open(readme_path, "w") as file:
                file.write(readme)
            repo.index.add([readme_path])
            repo.index.commit("Initial commit")
        # create new branch
        repo.create_head(branch)
        repo.remotes.origin.push(branch)
    repo.git.checkout(branch)

    return repo

@otel_tracer.start_as_current_span("main")
def main():

    parser = argparse.ArgumentParser(
        prog = 'schema_scraper',
        description= 'Extracts schema.org meta data from research data repositories.',
    )
    parser.add_argument('--config', '-c',
                        type=pathlib.Path,
                        default='config.yml',
                        help='config file that defines repositories to scrape')
    args = parser.parse_args()

    try:
        if not os.path.isfile(args.config):
            raise FileNotFoundError(f"Config file {args.config} does not exist.")

        # load config
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)

        # setup git repo
        git_repo = setup_git_repo(config['git'])

        # scrape sites
        git_repo.remotes.origin.pull()
        for sitemap in config['sitemaps']:
            scrape_repo_and_commit_to_git(sitemap['name'], sitemap['url'], git_repo)
        git_repo.remotes.origin.push()
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