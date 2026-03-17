import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium", app_title="Cloudflare Crawl API Analysis")


@app.cell
def _():
    import json
    import marimo as mo
    from pathlib import Path

    data_dir = Path("data")
    return Path, data_dir, json, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Cloudflare Crawl API Analysis

    This notebook explores how it appears the Cloudflare Crawl service will crawl a website. I used my own website as a target and ran several crawls in one day to see what data was collected, and what the web server logs looked like.

    ## Crawl Results

    Lets write some functions to help us analyze the Cloudflare Crawl data that we've downloaded for each snapshot.

    `get_records()` is an iterator for grabbing each record from the downloaded data.
    """)
    return


@app.cell
def _(data_dir, json):
    def get_records(snapshot_dir, status=None):
        for json_file in snapshot_dir.glob("*.json"):
            result = json.load(json_file.open("r"))
            for record in result["result"]["records"]:
                if status is None or record['status'] == status:
                    yield record

    next(get_records(data_dir / "20260312_1313"))
    return (get_records,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    `summarize_records()` will take the records iterator, and count the number of unique URLs that were included as well as the counts by status:
    """)
    return


@app.cell
def _(data_dir, get_records):
    from collections import Counter

    def summarize_records(records):
        urls = set()
        status = Counter()

        for rec in records:
            status[rec["status"]] += 1
            urls.add(rec["url"])

        result = dict(status.most_common())
        result['unique'] = len(urls)

        return result

    summarize_records(get_records(data_dir / "20260312_1313"))
    return (summarize_records,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Now we can run the summarization for each snapshot:
    """)
    return


@app.cell
def _(data_dir, get_records, summarize_records):
    for snapshot_dir in sorted(data_dir.iterdir()):
        print(f"snapshot: {snapshot_dir}")
        print(summarize_records(get_records(snapshot_dir)))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    It seems a bit strange that each run seemed to yield different output?

    ## Web Logs

    We can also look at what the activity was like by observing the web logs. I partitioned the web log for each run into the snapshot directory. The web log can be turned into a DataFrame.
    """)
    return


@app.cell
def _(data_dir):
    import re
    import pandas
    import datetime
    import time

    log_pattern = re.compile(
        r'^([0-9.]+) .* \[(.+)\] "GET (.+) HTTP/1.1" (\d+) (\d+).*$'
    )


    def log_dataframe(snapshot_dir):
        messages = []

        for line in (snapshot_dir / "web.log").open():
            if match := log_pattern.match(line):

                message = dict(
                    zip(
                        ["ip", "datetime", "url", "status", "bytes"],
                        match.groups(),
                    )
                )

                # parse datetime format: e.g. 12/Mar/2026:13:39:15 +0000
                message['datetime'] = message['datetime'].replace(' +0000', '')
                message["datetime"] = datetime.datetime.strptime(message["datetime"], '%d/%b/%Y:%H:%M:%S')

                message["url"] = "https://inkdroid.org" + message["url"]

                messages.append(message)

        return pandas.DataFrame(messages)

    df = log_dataframe(data_dir / "20260312_1313")
    df
    return df, log_dataframe, pandas, re


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We can see how many IP addresses were involved in the crawling, and how many requests they performed:
    """)
    return


@app.cell
def _(df):
    df.value_counts("ip")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Now we can see how many unique URLs were requested for the crawl, and what amount of duplication there was:
    """)
    return


@app.cell
def _(df):
    len(df.url.unique())
    return


@app.cell
def _(df):
    len(df.url.unique()) / len(df)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Only 29% of the requests for this snapshot were unique! This is because the crawlers constantly request the same CSS and JavaScript needed for rendering each page. The requests for HTML only happened once.
    """)
    return


@app.cell
def _(df):
    html_requests = df[df.url.str.match(r'.*/$')]
    len(html_requests.url.unique()) / len(html_requests)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We can look at how many requests happened over time by bucketing them.
    """)
    return


@app.cell
def _(mo):
    import altair as alt

    def requests_chart(df, title) -> alt.Chart:
        reqs_per_sec = df.set_index('datetime').resample('1min').count()['ip'].reset_index()    
        chart = mo.ui.altair_chart(
            alt.Chart(reqs_per_sec, title=title)
                .mark_line(interpolate='monotone')
                .encode(
                    x=alt.X(
                        'datetime',
                        axis=alt.Axis(
                            format='%Y-%m-%d %H:%M:%S',
                            title='Time',
                            labelAngle=-45
                        )
                    ),
                    y=alt.Y(
                        'ip',
                        title='Requests / Minute'
                    )
                )
        )

        return chart


    return (requests_chart,)


@app.cell
def _(data_dir, log_dataframe, requests_chart):
    def req_charts():
        for snapshot_dir in sorted(data_dir.iterdir()):
            df = log_dataframe(snapshot_dir)
            if len(df) > 0:
                requests_chart(df, snapshot_dir.name).display()

    req_charts()
    return


@app.cell
def _(data_dir, log_dataframe, requests_chart):
    def req_chart():    
        df = log_dataframe(data_dir / '20260313_1650')
        requests_chart(df, 'Snapshot 2026-03-14').display()

    req_chart()
    return


@app.cell
def _(data_dir, log_dataframe):
    def snap_ips(snap_dir):    
        df = log_dataframe(snap_dir)
        return df.value_counts('ip')

    snap_ips(data_dir / '20260313_1650')
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Results Comparison

    I ran data collection for https://inkdroid.org on multiple occasions, but they didn't all yield the same number of records.
    """)
    return


@app.cell
def _(data_dir, get_records, pandas, summarize_records):
    def record_counts():
        results = []
        for site_dir in data_dir.iterdir():
            #records = list(get_records(site_dir))
            summ = summarize_records(get_records(site_dir))
            summ['name'] = site_dir.name
            results.append(summ)

        df = pandas.DataFrame(results)
        df = df.sort_values('name')

        df = df[['name', 'completed', 'skipped', 'queued', 'errored', 'unique']]
        return df

    record_counts()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## URLS

    I can use the list of known URLs for my site, and one of the most successful results files to see how much was crawled.
    """)
    return


@app.cell
def _(Path, data_dir, get_records, re):
    from urllib.parse import urljoin

    def site_urls():
        site_dir = Path("/Users/edsu/Projects/inkdroid.org/_site")
        for root, dirnames, files in site_dir.walk():
            for file in files:
                if not file.endswith('.html'):
                    continue
                path = root.relative_to(site_dir) / file
                url = urljoin("https://inkdroid.org", str(path))
                url = re.sub(r'index.html$', '', url)
                yield url

    actual_urls = set(site_urls())

    urls_20260313_1650 = set([
        result['url'] 
        for result in get_records(data_dir / "20260313_1650", status='completed')
    ])

    for url in actual_urls - urls_20260313_1650:
        print(url)

    return actual_urls, urls_20260313_1650


@app.cell
def _(actual_urls, urls_20260313_1650):
    len(actual_urls - urls_20260313_1650) / len(actual_urls)
    return


@app.cell
def _():
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## HTML

    How does the HTML for different pages look?
    """)
    return


if __name__ == "__main__":
    app.run()
