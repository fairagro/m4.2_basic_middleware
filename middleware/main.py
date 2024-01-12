"""
The main script file for the FAIRagro basic middleware.
"""

import os
import sys
from pathlib import Path
import datetime
import argparse
import json
import logging
from typing import Tuple

import asyncio
import aiofiles
import pytz
import yaml
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

# Disable pylint warning that imports are not on top. But we need to adapt the import path before.
# Is there another solution so packages next top the main script can be found?
# pylint: disable=wrong-import-position
from metadata_scraper import MetadataScraperConfig, scrape_repo
from http_session import HttpSessionConfig
from git_repo import GitRepo, GitRepoConfig


def setup_opentelemetry(otlp_config: dict) -> None:
    """
    Setup OpenTelemetry for tracing.

    Arguments
    ---------
        otlp_config : dict
            A dictionary containing the configuration for OpenTelemetry.
            Currenlty only the 'endpoint' key is supported.
    """

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

    # Note: we would like to create a synchronous gauge to report the number of datasets within
    # each repo. Unfortunately the OpenTelemetry Python SDK does not support this yet. We could
    # try to work around with an observable gauge, but this is far from ideal.
    #
    # Initialize OpenTelemetry for Metrics to Console
    # metrics.set_meter_provider(
    #     MeterProvider(metrics_readers=[PeriodicExportingMetricReader(ConsoleMetricExporter())])
    # )
    # otel_meter = metrics.get_meter("FAIRagro.middleware.meter")


async def scrape_repo_and_write_to_file(
        folder_path: str,
        scraper_config: MetadataScraperConfig,
        default_http_config: HttpSessionConfig) -> Tuple[str, datetime.datetime]:
    """
    Scrapes research repository metadata and writes it to a file.

    Arguments
    ---------
        folder_path : str
            The folder path where the file should be saved.
        scraper_config : dict
            The configuration for the metadata scraper.
        http_config : dict
            The configuration for the HTTP client.

    Returns
    -------
        Tuple[str, datetime.datetime]
            A tuple containing the file path and the start timestamp.
    """
    start_timestamp = datetime.datetime.now(pytz.UTC)
    metadata, report = await scrape_repo(scraper_config, default_http_config)
    # We should collect some metrics data, but OpenTelemetry does not yet support transmitting
    # simple synchronous gauge values.
    # count_sites = len(sites)
    # count_metadata = len(metadata)
    path = os.path.join(folder_path, f'{scraper_config.name}.json')
    async with aiofiles.open(path, 'w', encoding='utf-8') as f:
        await f.write(json.dumps(metadata, indent=2, ensure_ascii=False, sort_keys=True))
    return path, start_timestamp, report

def commit_to_git(sitemap_url: str,
                  git_repo: GitRepo,
                  path: str,
                  starttime: datetime) -> None:
    """
    Create a log message and commit file to git.

    Arguments
    ---------
        sitemap_url : str
            The URL of the sitemap.
        git_repo : GitRepo
            The git repository.
        path : str
            The path of the file to commit.
        starttime : datetime
            The time the scraper started.

    Returns
    -------
        None
    """
    formatted_time = starttime.strftime('%Y-%m-%d %H:%M:%S.%f %Z%z')
    msg = (
        f'harvested by FAIRargo middleware at {formatted_time} from {sitemap_url}'
    )
    git_repo.add_and_commit([path], msg)

def setup_andconfig() -> dict:
    """
    This function will perform setup work and reads the configuration file.
    """

    try:
        parser = argparse.ArgumentParser(
            prog = 'fairagro-middleware',
            description= 'Extracts schema.org meta data from research data repositories.',
        )
        parser.add_argument('--config', '-c',
                            type=Path,
                            default='config.yml',
                            help='Config file for this tool.')
        parser.add_argument(
            '--git',
            action=argparse.BooleanOptionalAction,
            default=True,
            help=(
                'Specify this flag to enabled or disable git interactions.'
                'If disabled the outout files will nevrtheless be written to git.local_path '
                'as specified within the config file.'
            )
        )
        args = parser.parse_args()

        if not os.path.isfile(args.config):
            raise FileNotFoundError(f'Config file {args.config} does not exist.')

        # load config
        with open(args.config, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        setup_opentelemetry(config['opentelemetry'])

        return args, config
    # pylint: disable-next=broad-except
    except Exception:
        logging.exception("An error occured during initialization")
        sys.exit(1)

async def main():
    """
    The main async function of the basic middleware
    """

    args, config = setup_andconfig()

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
                local_path = config['git']['local_path']
                os.makedirs(local_path, exist_ok=True)

            default_http_config = HttpSessionConfig(**config['http_client'])
            full_report = []
            # scrape sites
            for sitemap in config['sitemaps']:
                scraper_config = MetadataScraperConfig(**sitemap)
                path, starttime, repo_report = await scrape_repo_and_write_to_file(
                    local_path, scraper_config, default_http_config)
                full_report += [{'repo_name': sitemap['name'] , **repo_report}]
                if git_repo:
                    commit_to_git(scraper_config.url, git_repo, path, starttime)

            if git_repo:
                git_repo.push()

            print(json.dumps(full_report, indent=2, ensure_ascii=False, sort_keys=True))
        # pylint: disable-next=broad-except
        except Exception as e:
            otel_span = trace.get_current_span()
            otel_span.record_exception(e)
            msg = "Error when scraping repositories"
            otel_span.add_event(msg)
            logging.exception(msg)
            sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
