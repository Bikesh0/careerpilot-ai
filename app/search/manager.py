from app.search.demo import DemoSearcher
from app.search.public_jobs import PublicJobProvider
from app.search.sources.remote_source import RemoteJobSource


class SearchManager:

    def __init__(self):

        self.searchers = [

            DemoSearcher(),

            PublicJobProvider(),

            RemoteJobSource()

        ]

    def search_jobs(self):

        jobs = []

        seen = set()

        for searcher in self.searchers:

            try:

                results = searcher.search()

                print(
                    f"{searcher.__class__.__name__} found {len(results)} jobs"
                )

                for job in results:

                    key = (

                        job.title.lower().strip(),

                        job.company.lower().strip()

                    )

                    if key in seen:
                        continue

                    seen.add(key)

                    jobs.append(job)

            except Exception as e:

                print(

                    f"{searcher.__class__.__name__} failed:",

                    e

                )

        print(f"Collected {len(jobs)} unique jobs")

        return jobs