import asyncio, aiofiles
import aiohttp
import chardet
import os, sys
from pathlib import Path, PurePosixPath
import datetime, pytz
import argparse
import yaml
import itertools
import extruct
import git
from w3lib.html import get_base_url
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import json
import logging
from opentelemetry import trace #, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.sampling import ALWAYS_ON
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
# from opentelemetry.sdk.metrics import MeterProvider
# from opentelemetry.sdk.metrics.export import (
#     ConsoleMetricExporter,
#     PeriodicExportingMetricReader,
# )
from opentelemetry.semconv.trace import SpanAttributes
import opentelemetry.instrumentation.requests
import opentelemetry.instrumentation.urllib
import opentelemetry.instrumentation.aiohttp_client


def setup_opentelemetry(otlp_config):
    # Initialize some automatic OpenTelemetry instrumentations.
    # Actually we only use aiohttp, but requests and urllib are indirect dependencies.
    # We we also instrument them in case they are used internally.
    opentelemetry.instrumentation.requests.RequestsInstrumentor().instrument()
    opentelemetry.instrumentation.urllib.URLLibInstrumentor().instrument()
    opentelemetry.instrumentation.aiohttp_client.AioHttpClientInstrumentor().instrument()

    endpoint = otlp_config.get('endpoint')
    if endpoint:
        # Initialize OpenTelemetry for Tracing to OTLP endpoint
        trace.set_tracer_provider(
            TracerProvider(
                resource=Resource.create({
                    "service.name": "FAIRagro middleware"
                }),
                active_span_processor=BatchSpanProcessor(
                    OTLPSpanExporter(endpoint=endpoint)
                ),
                sampler=ALWAYS_ON
            )
        )
    else:
        trace.set_tracer_provider(TracerProvider())

    # Note: we would like to create a synchronous gauge to report the number of datasets within each repo.
    # Unfortunately the OpenTelemetry Python SDK does not support this yet. We could try to work around with
    # an observable gauge, but this is far from ideal.
    #
    # Initialize OpenTelemetry for Metrics to Console
    # metrics.set_meter_provider(
    #     MeterProvider(metrics_readers=[PeriodicExportingMetricReader(ConsoleMetricExporter())])
    # )
    # otel_meter = metrics.get_meter("FAIRagro.middleware.meter")

def make_path_absolute(path):
    if path and not os.path.isabs(path):
        # we assume that relative paths are relative to the script directory, not to the current working directory
        script_dir = os.path.dirname(os.path.realpath(__file__))
        return os.path.normpath(os.path.join(script_dir, path))
    return path


async def get_url(url, session):
    async with session.get(url) as response:
        content = await response.read()
        # Detect the encoding of the content, so we do not need to rely on HTTP content-type
        # (which used to be wrong for e!DAL)
        encoding = chardet.detect(content)['encoding']
        return content.decode(encoding)

async def extract_sites(sitemap_url, session):
    sitemap_xml = await get_url(sitemap_url, session)
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

async def extract_schema_org_or_log_error(url, session):
    with trace.get_tracer(__name__).start_as_current_span("extract_schema_org_or_issue_error") as otel_span:
        otel_span.set_attribute(SpanAttributes.URL_FULL, url)
        try:
            content = await get_url(url, session)
            metadata = extract_schema_org_jsonld(content, url)
            return metadata
        except Exception as e:
            suspicious_jsonld = ''.join(extract_jsonld(content))
            otel_span.set_attribute("FAIRagro.middleware.suspicious_jsonld", suspicious_jsonld)
            otel_span.record_exception(e)
            msg = "Could not extract schema.org meta data in JSON-LD format"
            otel_span.add_event(msg)
            logging.error(f"{msg}, url: {url}, supicius JSON-LD:\n{suspicious_jsonld}")
            return None
 
async def extract_many_schema_org(urls, session):
    result = await asyncio.gather(*[ extract_schema_org_or_log_error(url, session) for url in urls ])
    # metadata might be None, if schema.org parser failed.
    # If metadata is not None, it's a list that may contain several JSON-LD entries.
    # e!DAL sometimes defines two entries: "@type":"Dataset" and "@type":"Taxon".
    return [ metadata for metadata in result if metadata is not None ]

async def scrape_repo_and_commit_to_git(name, sitemap_url, git_repo, session):
    with trace.get_tracer(__name__).start_as_current_span("scrape_repo_and_commit_to_git") as otel_span:
        otel_span.set_attribute("FAIRagro.middleware.repository_name", name)
        otel_span.set_attribute("FAIRagro.middleware.repository_sitemap_url", sitemap_url)
        start_timestamp = datetime.datetime.now(pytz.UTC)        
        sites = await extract_sites(sitemap_url, session)
        metadata = await extract_many_schema_org(sites, session)
        # We should collect some metrics data, but OpenTelemetry does not yet support transmitting
        # simple synchronous gauge values.
        # count_sites = len(sites)
        # count_metadata = len(metadata)
        result = list(itertools.chain.from_iterable(metadata))
        path = os.path.join(git_repo.working_dir, f'{name}.json')
        async with aiofiles.open(path, 'w') as f:
            await f.write(json.dumps(result, indent=2))
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
    # find out local repo path
    local_path = make_path_absolute(repo_info['local_path'])

    # find the ssh key and use it
    ssh_key_path = make_path_absolute(repo_info.get('ssh_key_path'))
    if ssh_key_path:
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


async def main():
    try:
        parser = argparse.ArgumentParser(
            prog = 'fairagro-middleware',
            description= 'Extracts schema.org meta data from research data repositories.',
        )
        parser.add_argument('--config', '-c',
                            type=Path,
                            default='config.yml',
                            help='config file for this tool')
        args = parser.parse_args()

        config_path = make_path_absolute(args.config)
        if not os.path.isfile(config_path):
            raise FileNotFoundError(f"Config file {config_path} does not exist.")
        
        # load config
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        setup_opentelemetry(config['opentelemetry'])
    except Exception as e:
        logging.exception("An error occured during initialization")
        sys.exit(1)

    with trace.get_tracer(__name__).start_as_current_span("main") as otel_span:
        try:
            # setup git repo
            git_repo = setup_git_repo(config['git'])

            # scrape sites
            git_repo.remotes.origin.pull()
            connection_limit = int(config.get('connection_limit', 100))
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=connection_limit)) as session:
                for sitemap in config['sitemaps']:
                    await scrape_repo_and_commit_to_git(
                        sitemap['name'], sitemap['url'], git_repo, session)
            git_repo.remotes.origin.push()
        except Exception as e:
            otel_span = trace.get_current_span()
            otel_span.record_exception(e)
            msg = "Error when scraping repositories"
            otel_span.add_event(msg)
            logging.exception(msg)
            sys.exit(1)
        
if __name__ == '__main__':
    asyncio.run(main())
