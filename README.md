This is a simplistic Python based  command line utility that will use [Cloudflare's Crawl API] to
crawl a website, and then fetch the results to the filesystem once the job is completed. It was created to help me test the Cloudflare service, and not to provide access to all the options that the service provides.

You run it like so:

```bash
uvx https://github.com/edsu/cloudflare-crawl/ crawl https://example.com
```

I guess if it is useful I could put it on pypi. But there are a lot of options in Cloudflare's API that would probably need command line equivalents.

Note: you will need to set these in your environment or in a `.env` file for 
the program to work:

- CLOUDFRONT_TOKEN
- CLOUDFRONT_ACCOUNT_ID

In order to create a token you will need to go to the Cloudfront dashboard and
create a token that has the `Browser Rendering:Edit` permission.

[Cloudflare's Crawl API]: https://developers.cloudflare.com/browser-rendering/rest-api/crawl-endpoint/
