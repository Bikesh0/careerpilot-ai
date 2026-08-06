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

        # Stores the latest search results
        self.latest_jobs = []

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

                    # Give every job a unique ID
                    job.id = len(jobs)

                    jobs.append(job)

            except Exception as e:

                print(

                    f"{searcher.__class__.__name__} failed:",

                    e

                )

        # Save latest jobs in memory
        self.latest_jobs = jobs

        print(f"Collected {len(jobs)} unique jobs")

        return jobs

    def get_job(self, job_id):

        if not self.latest_jobs:
            return None

        if job_id < 0:
            return None

        if job_id >= len(self.latest_jobs):
            return None

        return self.latest_jobs[job_id]