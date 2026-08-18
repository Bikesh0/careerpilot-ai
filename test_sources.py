from app.search.sources.web_sources import (
    JoblySource,
    TyomarkkinatoriSource,
    WorkInFinlandSource,
)

# DuunitoriSource is deliberately not included here.
#
# duunitori.fi/robots.txt disallows this scraper's user-agent (see
# docs/DATA_SOURCES.md) - it's unregistered from V1/V2 search for the
# same reason, and this manual smoke-check script must not run it live
# either. Do not re-add it without resolving that first.
sources = [
    JoblySource(),
    TyomarkkinatoriSource(),
    WorkInFinlandSource(),
]

for source in sources:
    print("\n###", source.__class__.__name__)

    try:
        jobs = source.search()

        print("TOTAL:", len(jobs))

        for job in jobs[:10]:
            print(
                job.title,
                "|",
                job.company,
                "|",
                job.location,
                "|",
                job.url
            )

    except Exception as error:
        print("ERROR:", error)