from app.search.sources.web_sources import (
    DuunitoriSource,
    JoblySource,
    TyomarkkinatoriSource,
    WorkInFinlandSource,
)

sources = [
    DuunitoriSource(),
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