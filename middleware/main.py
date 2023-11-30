import asyncio, aiofiles
import os, sys
from pathlib import Path
import datetime, pytz
import argparse
import yaml
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
import opentelemetry.instrumentation.requests
import opentelemetry.instrumentation.urllib
import opentelemetry.instrumentation.aiohttp_client

# add the script directory to the python module path
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from metadata_scraper import MetadataScraper, MetadataScraperConfig
from git_repo import GitRepo, GitRepoConfig
from utils import make_path_absolute


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


async def scrape_repo_and_write_to_file(folder_path, scraper_config, http_config):
    start_timestamp = datetime.datetime.now(pytz.UTC)        
    scraper = MetadataScraper(scraper_config, http_config)
    metadata = await scraper.scrape_repo()
    # We should collect some metrics data, but OpenTelemetry does not yet support transmitting
    # simple synchronous gauge values.
    # count_sites = len(sites)
    # count_metadata = len(metadata)
    path = os.path.join(folder_path, f"{scraper_config.name}.json")
    async with aiofiles.open(path, 'w', encoding='utf-8') as f:
        await f.write(json.dumps(metadata, indent=2, ensure_ascii=False))
    return path, start_timestamp

def commit_to_git(name, sitemap_url, git_repo, path, starttime):
    formatted_time = starttime.strftime('%Y-%m-%d %H:%M:%S.%f %Z%z')
    msg = f"FAIRagro middleware scraper for repo '{name}' with sitemap {sitemap_url}, started at {formatted_time}"
    git_repo.add_and_commit([path], msg)

async def main():
    try:
        parser = argparse.ArgumentParser(
            prog = 'fairagro-middleware',
            description= 'Extracts schema.org meta data from research data repositories.',
        )
        parser.add_argument('--config', '-c',
                            type=Path,
                            default='config.yml',
                            help='Config file for this tool.')
        parser.add_argument('--git',
                            action=argparse.BooleanOptionalAction,
                            default=True,
                            help='Specify this flag to enabled or disable git interactions.'
                                    'If disabled the outout files will nevrtheless be written to git.local_path '
                                    'as specified within the config file.'),
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
            # setup git repo if desired
            if args.git:
                git_config = GitRepoConfig(**config['git'])
                git_repo = GitRepo(git_config)
                local_path = git_repo.working_dir
                git_repo.pull()
            else:
                git_repo = None
                local_path = make_path_absolute(config['git']['local_path'])
                os.makedirs(local_path, exist_ok=True)

            # scrape sites
            for sitemap in config['sitemaps']:
                scraper_config = MetadataScraperConfig(**sitemap)
                path, starttime = await scrape_repo_and_write_to_file(
                    local_path, scraper_config, config['http_client'])
                if git_repo:
                    commit_to_git(scraper_config.name, scraper_config.url, git_repo, path, starttime)
            
            if git_repo:
                git_repo.push()
        except Exception as e:
            otel_span = trace.get_current_span()
            otel_span.record_exception(e)
            msg = "Error when scraping repositories"
            otel_span.add_event(msg)
            logging.exception(msg)
            sys.exit(1)
        
if __name__ == '__main__':
    asyncio.run(main())
