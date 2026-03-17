import json
import os
import time
from pathlib import Path
from typing import Annotated

import dotenv
import requests
import typer
from requests.adapters import HTTPAdapter, Retry


# load environment variables
dotenv.load_dotenv()
token = os.environ.get("CLOUDFRONT_TOKEN")
account_id = os.environ.get("CLOUDFRONT_ACCOUNT_ID")
headers = {"Authorization": f"Bearer {token}"}

# set up http client, with retries for 401 which have been observed
https = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[401])
https.mount("https://", HTTPAdapter(max_retries=retries))

# the cli app
app = typer.Typer()


@app.command()
def crawl(
    url: str,
    download_dir: Annotated[
        Path | None, typer.Option(file_okay=False, dir_okay=True, exists=False)
    ] = None,
) -> None:
    """
    Start a crawl for a website URL, wait for it to be completed and then
    download the data.
    """

    if token is None or account_id is None:
        print(
            "Please set CLOUDFRONT_ACCOUNT_ID and CLOUDFRONT_TOKEN environment variables"
        )
        return

    job_id = start_crawl(url)
    print(f"created job {job_id}")

    wait_for_job(job_id)
    print(f"job {job_id} completed")

    write_results(job_id, download_dir)


@app.command()
def status(job_id: str):
    """
    Check the status of a job_id.
    """
    job = get_job(job_id)["result"]
    for name, value in job.items():
        if name != "records":
            print(f"{name}: {value}")


@app.command()
def download(
    job_id: str,
    download_dir: Annotated[
        Path | None, typer.Option(file_okay=False, dir_okay=True, exists=False)
    ] = None,
):
    """
    Download data related to a job_id.
    """
    write_results(job_id, download_dir)


def start_crawl(url: str):
    data = {"url": url, "formats": ["html", "markdown"], "limit": 5000}

    resp = https.post(
        f"https://api.cloudflare.com/client/v4/accounts/{account_id}/browser-rendering/crawl",
        headers=headers,
        json=data,
    )

    resp.raise_for_status()

    result = resp.json()

    if result["success"] is False:
        raise Exception(result)

    return result["result"]


def wait_for_job(job_id: str, sleep_secs=60) -> str:
    """
    Wait for the crawl job to stop running and return the status.
    """
    while True:
        result = get_job(job_id, params={"limit": 1})

        if result["result"]["status"] != "running":
            return result["result"]["status"]
        else:
            total = int(result["result"]["total"])
            finished = int(result["result"]["finished"])
            skipped = int(result["result"]["skipped"])
            print(
                f"waiting for {job_id} to complete: total={total} finished={finished} skipped={skipped}"
            )
            time.sleep(sleep_secs)


def write_results(job_id: str, download_dir: Path | None) -> None:
    """
    Fetch the results of the crawl job and write them as JSON to the filesystem.
    """
    if download_dir is None:
        download_dir = Path(".")

    if not download_dir.is_dir():
        download_dir.mkdir(parents=True)

    cursor = None
    count = 0

    params = {"limit": 1000}

    while True:
        if cursor is not None:
            params["cursor"] = cursor

        resp = https.get(
            f"https://api.cloudflare.com/client/v4/accounts/{account_id}/browser-rendering/crawl/{job_id}",
            params=params,
            headers=headers,
        )

        resp.raise_for_status()

        count += 1
        result = resp.json()
        path = download_dir / f"{job_id}-{count:03}.json"

        json.dump(result, path.open("w"), indent=2)
        print(f"wrote {path}")

        new_cursor = result["result"].get("cursor")
        if new_cursor is None:
            break
        elif new_cursor == cursor:
            break
        else:
            cursor = new_cursor


def get_job(job_id: str, params={}) -> dict:
    resp = https.get(
        f"https://api.cloudflare.com/client/v4/accounts/{account_id}/browser-rendering/crawl/{job_id}",
        params={"limit": 1},
        headers=headers,
    )

    resp.raise_for_status()

    return resp.json()


if __name__ == "__main__":
    app()
