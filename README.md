[![CI](https://github.com/edsu/cloudflare-crawl/actions/workflows/ci.yml/badge.svg)](https://github.com/edsu/cloudflare-crawl/actions/workflows/ci.yml)

This is a simplistic Python based  command line utility that will use [Cloudflare's Crawl API] to
crawl a website, and then fetch the results to the filesystem once the job is completed. It was created [to help me test] the Cloudflare service, and not to provide access to all the options that the service provides.

You run it like this, which will create the job, poll till its complete, and then download the data:

```text
uvx https://github.com/edsu/cloudflare-crawl/ crawl https://example.com

created job 36f80f5e-d112-4506-8457-89719a158ce2
waiting for 36f80f5e-d112-4506-8457-89719a158ce2 to complete: total=1520 finished=837 skipped=1285
waiting for 36f80f5e-d112-4506-8457-89719a158ce2 to complete: total=1537 finished=868 skipped=1514
...
wrote 36f80f5e-d112-4506-8457-89719a158ce2-001.json
wrote 36f80f5e-d112-4506-8457-89719a158ce2-002.json
wrote 36f80f5e-d112-4506-8457-89719a158ce2-003.json
wrote 36f80f5e-d112-4506-8457-89719a158ce2-004.json
wrote 36f80f5e-d112-4506-8457-89719a158ce2-005.json
```

If you can't wait for it to complete you can also check up on a crawl using its ID:

```shell
uvx https://github.com/edsu/cloudflare-crawl/ status 36f80f5e-d112-4506-8457-89719a158ce2

id: 36f80f5e-d112-4506-8457-89719a158ce2
status: completed
browserSecondsUsed: 1382.8220786132817
total: 1967
finished: 1967
skipped: 6862
cursor: 1
```

Similarly you can initiate the download separately once the job is complete:

```
uvx https://github.com/edsu/cloudflare-crawl/ download 36f80f5e-d112-4506-8457-89719a158ce2

wrote 36f80f5e-d112-4506-8457-89719a158ce2-001.json
wrote 36f80f5e-d112-4506-8457-89719a158ce2-002.json
wrote 36f80f5e-d112-4506-8457-89719a158ce2-003.json
wrote 36f80f5e-d112-4506-8457-89719a158ce2-004.json
wrote 36f80f5e-d112-4506-8457-89719a158ce2-005.json
```

I guess if this proves useful to others I could put it on pypi. But there are a lot of options in Cloudflare's API that would probably need command line equivalents.

Note: you will need to set these in your environment or in a `.env` file for 
the program to work:

- CLOUDFRONT_TOKEN
- CLOUDFRONT_ACCOUNT_ID

In order to create a token you will need to go to the Cloudfront dashboard and
create a token that has the `Browser Rendering:Edit` permission.

The analysis directory contains a Marimo notebook and some data for evaluating the crawling behavior of the service.

[Cloudflare's Crawl API]: https://developers.cloudflare.com/browser-rendering/rest-api/crawl-endpoint/
[to help me test]: https://inkdroid.org/2026/03/16/seeing-the-web/
