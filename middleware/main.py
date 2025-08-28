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
from typing import Dict, Tuple
import tempfile

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

# add the script directory to the python module path
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

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
) -> Tuple[Path, datetime.datetime, Dict]:
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
    path = Path(os.path.join(folder_path, f"{scraper_config.name}.json"))
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(
            json.dumps(metadata, indent=2, ensure_ascii=False, sort_keys=True)
        )
    return path, start_timestamp, report


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


def transform_publisso_to_publisso_schemaorg():
    """
    Transform the Publisso metadata to schema.org format.
    """

    # Archivos
    input_file = Path("./output/publisso.json").resolve()
    jq_script = Path("./scripts/publiso_conversor.jq").resolve()

    if not input_file.exists():
        print(f"❌ Archivo de entrada no encontrado: {input_file}")
        return

    # Crear directorio de salida si no existe
    input_file.parent.mkdir(parents=True, exist_ok=True)

    # Usar archivo temporal para el resultado
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, dir=input_file.parent, suffix=".json"
    ) as tmp_file:
        tmp_path = Path(tmp_file.name)

    try:
        # Ejecutar jq en memoria usando context managers so resources are cleaned up
        with subprocess.Popen(
            ["jq", "-f", str(jq_script), str(input_file)],
            stdout=subprocess.PIPE,
            text=True
        ) as p1:
            with open(tmp_path, "w", encoding="utf-8") as outfile:
                with subprocess.Popen(
                    ["jq", "-s", "."],
                    stdin=p1.stdout,
                    stdout=outfile,
                    text=True
                ) as p2:
                    if p1.stdout is not None:
                        p1.stdout.close()  # Permite que p1 reciba SIGPIPE si p2 falla
                    p2.communicate()

                    if p1.wait() != 0:
                        raise RuntimeError(f"jq script failed with exit code {p1.returncode}")
                    if p2.returncode != 0:
                        raise RuntimeError(f"jq merge failed with exit code {p2.returncode}")

        # Reemplazar archivo original
        os.remove(input_file)  # Eliminar input original
        tmp_path.rename(input_file)  # Renombrar temp como input original

        print(
            f"✅ Transformación completada, archivo actualizado: {input_file}")

    except subprocess.CalledProcessError as e:
        print(f"❌ Error al ejecutar jq: {e}")
        if tmp_path.exists():
            tmp_path.unlink()


def extract_thunen_from_openagrar_metadata():
    """
    Extract Thünen metadata from OpenAgrar metadata.
    """
    # Configuration
    input_file = Path("./output/openagrar.json").resolve()
    output_file = Path("./output/thunen.json").resolve()

    if not input_file.exists():
        print(f"❌ Archivo de entrada no encontrado: {input_file}")
        return
    # Regex pattern to match publisher synonyms
    publisher_pattern = re.compile(
        r"Thünen[- ]?Institut|Thuenen Institute|Thünen-Atlas", re.IGNORECASE
    )

    # Load JSON
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Found {len(data)} datasets in {input_file}")
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
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)

    # Update original file with remaining datasets
    with open(input_file, "w", encoding="utf-8") as f:
        json.dump(remaining, f, ensure_ascii=False, indent=2)

    print(f"Extracted {len(filtered)} datasets to {output_file}")
    print(f"{len(remaining)} datasets remain in {input_file}")


async def main():
    """
    The main async function of the basic middleware
    """

    args, config = setup_and_config()

    with trace.get_tracer(__name__).start_as_current_span("main") as otel_span:
        try:
            # setup git repo if desired
            if args.git:
                git_config = GitRepoConfig(**config["git"])
                git_repo = GitRepo(git_config)
                local_path = git_repo.working_dir
                git_repo.pull()
            else:
                git_repo = None
                local_path = config.get("git", {}).get("local_path", "/tmp/middleware_git")
                os.makedirs(local_path, exist_ok=True)

            default_http_config = HttpSessionConfig(**config["http_client"])
            full_report = []
            # scrape sites
            for sitemap in config["sitemaps"]:
                scraper_config = MetadataScraperConfig(**sitemap)
                path, starttime, repo_report = await scrape_repo_and_write_to_file(
                    Path(local_path), scraper_config, default_http_config
                )
                full_report += [{"repo_name": sitemap["name"], **repo_report}]
                if sitemap["name"] == "publisso":
                    transform_publisso_to_publisso_schemaorg()
                if sitemap["name"] == "openagrar":
                    extract_thunen_from_openagrar_metadata()
                commit = sitemap.get("commit", True)
                if git_repo and commit:
                    # if a git repo is set, commit all files except those that are explicitly
                    # excluded
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


if __name__ == "__main__":
    asyncio.run(main())
