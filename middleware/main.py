"""
The main script file for the FAIRagro basic middleware.
"""
import os
import sys
from pathlib import Path
import datetime
import argparse
import json
import re
import logging
import subprocess
from typing import Dict, List, Tuple

import asyncio

import aiofiles
import pytz
import yaml
from opentelemetry import trace  # , metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.sampling import ALWAYS_ON
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

import opentelemetry.instrumentation.requests
import opentelemetry.instrumentation.urllib
import opentelemetry.instrumentation.aiohttp_client

from middleware.git_repo import GitRepo, GitRepoConfig
from middleware.http_session import HttpSessionConfig
from middleware.metadata_scraper import MetadataScraperConfig, scrape_repo
from middleware.utils.tracer import traced

# add the script directory to the python module path
#sys.path.append(os.path.dirname(os.path.realpath(__file__)))

# Disable pylint warning that imports are not on top. But we need to adapt the import path before.
# Is there another solution so packages next top the main script can be found?
# pylint: disable=wrong-import-position


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

    endpoint = otlp_config.get("endpoint")
    insecure = otlp_config.get("insecure", False)
    if endpoint:
        # Initialize OpenTelemetry for Tracing to OTLP endpoint
        provider = TracerProvider(
            resource=Resource.create(
                {"service.name": "FAIRagro middleware"}
            ),
            sampler=ALWAYS_ON
        )
        provider.add_span_processor(
            BatchSpanProcessor(
                OTLPSpanExporter(endpoint=endpoint, insecure=insecure))
        )
        trace.set_tracer_provider(provider)
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
    folder_path: Path,
    scraper_config: MetadataScraperConfig,
    default_http_config: HttpSessionConfig,
) -> Tuple[Path | None, datetime.datetime, Dict]:
    """
    Scrapes research repository metadata and writes it to a file.

    Arguments
    ---------
        folder_path : Path
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
    if metadata:
        path = folder_path / f"{scraper_config.name}.json"
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(
                json.dumps(metadata, indent=2, ensure_ascii=False, sort_keys=True)
            )
        return path, start_timestamp, report

    return None, start_timestamp, report


def commit_to_git(
    sitemap_url: str, git_repo: GitRepo, path: Path, starttime: datetime.datetime
) -> None:
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
    formatted_time = starttime.strftime("%Y-%m-%d %H:%M:%S.%f %Z%z")
    msg = f"harvested by FAIRargo middleware at {formatted_time} from {sitemap_url}"
    git_repo.add_and_commit([path], msg)


def setup_and_config() -> Tuple[argparse.Namespace, Dict]:
    """
    This function will perform setup work and reads the configuration file.
    """

    try:
        parser = argparse.ArgumentParser(
            prog="fairagro-middleware",
            description="Extracts schema.org meta data from research data repositories.",
        )
        parser.add_argument(
            "--config",
            "-c",
            type=Path,
            default="config.yml",
            help="Config file for this tool.",
        )
        parser.add_argument(
            "--git",
            action=argparse.BooleanOptionalAction,
            default=True,
            help=(
                "Specify this flag to enabled or disable git interactions."
                "If disabled the outout files will nevrtheless be written to git.local_path "
                "as specified within the config file."
            ),
        )
        args = parser.parse_args()

        if not os.path.isfile(args.config):
            raise FileNotFoundError(
                f"Config file {args.config} does not exist.")

        # load config
        with open(args.config, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        setup_opentelemetry(config["opentelemetry"])

        return args, config
    # pylint: disable-next=broad-except
    except Exception:
        logging.exception("An error occured during initialization")
        sys.exit(1)


def transform_publisso_to_publisso_schemaorg(
    input_file: Path,
    original_report: Dict
) -> Tuple[List[Path], List[Dict]]:
    """
    Transform the Publisso metadata to schema.org format.
    """

    # Archivos
    output_file = input_file.parent / "publisso.json"
    jq_script = Path(__file__).parent / "scripts/publiso_conversor.jq"

    if not input_file.exists():
        logging.warning("❌ Archivo de entrada no encontrado: %s", input_file)
        return ([],[])

    try:
        # Ejecutar jq en memoria usando context managers so resources are cleaned up
        with subprocess.Popen(
            ["jq", "-f", str(jq_script), str(input_file)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        ) as p1:
            with open(output_file, "w", encoding="utf-8") as outfile:
                with subprocess.Popen(
                    ["jq", "-s", "."],
                    stdin=p1.stdout,
                    stdout=outfile,
                    stderr=subprocess.PIPE,
                    text=True
                ) as p2:
                    if p1.stdout is not None:
                        p1.stdout.close()  # Permite que p1 reciba SIGPIPE si p2 falla
                    _, err2 = p2.communicate()
                    _, err1 = p1.communicate()

                    if p1.wait() != 0:
                        logging.error(
                            "jq script failed with exit code %s. stderr: %s",
                            p1.returncode, err1)
                        # Do not return, just log the error and continue, as it could be
                        # that the output is still valid
                        # return ([],[])
                    if p2.returncode != 0:
                        logging.error(
                            "jq merge failed with exit code %s. stderr: %s",
                            p2.returncode, err2)
                        # Do not return, just log the error and continue, as it could be
                        # that the output is still valid
                        # return ([],[])
    except subprocess.CalledProcessError as e:
        logging.error("❌ Error al ejecutar jq: %s", str(e))
        return ([],[])

    logging.info(
        "✅ Transformación completada, archivo actualizado: %s", input_file
    )

    repo_report = [{"repo_name": "publisso", **original_report}]
    return ([output_file], repo_report)


def extract_thunen_from_openagrar_metadata(
    input_file: Path
) -> Tuple[List[Path], List[Dict]]:
    """
    Extract Thünen metadata from OpenAgrar metadata.
    """
    # Configuration
    thunen_out = input_file.parent / "thunen_atlas.json"
    openagrar_out = input_file.parent / "openagrar.json"

    if not input_file.exists():
        logging.warning("❌ Archivo de entrada no encontrado: %s", input_file)
        return ([],[])
    # Regex pattern to match publisher synonyms
    publisher_pattern = re.compile(
        r"Thünen[- ]?Institut|Thuenen Institute|Thünen-Atlas", re.IGNORECASE
    )

    # Load JSON
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    logging.info("Found %s datasets in %s", len(data), input_file)
    # Separate datasets
    filtered = []
    remaining = []
    for dataset in data:
        publisher_name = dataset.get("publisher", {}).get("name", "")
        if publisher_pattern.search(publisher_name):
            filtered.append(dataset)
        else:
            remaining.append(dataset)

    # Write filtered datasets to new file
    with open(thunen_out, "w", encoding="utf-8") as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)

    # Update original file with remaining datasets
    with open(openagrar_out, "w", encoding="utf-8") as f:
        json.dump(remaining, f, ensure_ascii=False, indent=2)

    logging.info("Extracted %s datasets to %s", len(filtered), thunen_out)
    logging.info("%s datasets remain in %s", len(remaining), openagrar_out)

    return (
        [thunen_out, openagrar_out],
        [
            {
                "repo_name": "thunen_atlas",
                "valid_entries": len(filtered),
                "failed_entries": 0,
                "skipped": False
            },
            {
                "repo_name": "openagrar",
                "valid_entries": len(remaining),
                "failed_entries": 0,
                "skipped": False
            }
        ]
    )

async def setup_repo(args, config):
    """
    Setup the git repository if configured and requested.
    """

    if args.git:
        git_config = GitRepoConfig(**config["git"])
        git_repo = GitRepo(git_config)
        local_path = Path(git_repo.working_dir)
        git_repo.pull()
    else:
        git_repo = None
        local_path = Path(config.get("git", {}).get("local_path", "/tmp/middleware_git"))
        os.makedirs(local_path, exist_ok=True)
    return git_repo, local_path


@traced
async def process_sitemap(sitemap, local_path, default_http_config, git_repo):
    """
    Process a single sitemap configuration.
    """

    scraper_config = MetadataScraperConfig(**sitemap)

    otel_span = trace.get_current_span()
    otel_span.set_attribute(
        "FAIRagro.middleware.sitemap_name", scraper_config.name)

    path, starttime, repo_report = await scrape_repo_and_write_to_file(
        local_path, scraper_config, default_http_config
    )

    if path:
        # Ugly special cases for known repositories that need post-processing.
        # We should find a more generic solution in the future.
        if "publisso" in scraper_config.name:
            paths, repo_reports = transform_publisso_to_publisso_schemaorg(path, repo_report)
            commit = True
        elif "openagrar" in scraper_config.name:
            paths, repo_reports = extract_thunen_from_openagrar_metadata(path)
            commit = True
        else:
            paths = [path]
            repo_reports = [{"repo_name": sitemap["name"], **repo_report}]
            commit = sitemap.get("commit", True)

        if git_repo and commit:
            for path in paths:
                commit_to_git(scraper_config.url, git_repo, path, starttime)
    else:
        repo_reports = [{"repo_name": sitemap["name"], **repo_report}]

    return repo_reports


@traced
async def main():
    """
    The main async function of the basic middleware
    """

    args, config = setup_and_config()

    try:
        git_repo, local_path = await setup_repo(args, config)
        default_http_config = HttpSessionConfig(**config["http_client"])

        full_report = []
        for sitemap in config["sitemaps"]:
            repo_reports = await process_sitemap(
                sitemap, local_path, default_http_config, git_repo
            )
            full_report.extend(repo_reports)

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


if __name__ == "__main__":
    asyncio.run(main())
