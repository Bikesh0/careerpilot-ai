from app.search.sources.remote_source import RemoteJobSource
from app.search.sources.greenhouse_source import GreenhouseSource
from app.search.sources.ashby_source import AshbySource
from app.search.search_profile import SearchProfile
from app.search.sources.web_sources import (
    DuunitoriSource,
    JoblySource,
)


class SearchManager:
    """
    Central job-search manager for CareerPilot AI.

    Responsibilities:
    - Create and maintain the SearchProfile.
    - Run all configured real job sources.
    - Handle individual source failures without stopping the
      complete search pipeline.
    - Remove duplicate real job postings.
    - Preserve the original job URL.
    - Assign local CareerPilot job IDs.
    - Store the latest search results.
    """

    def __init__(self):
        self.search_profile = SearchProfile()

        self.searchers = [
            AshbySource(),
            GreenhouseSource(),
            RemoteJobSource(),

            # Real Finnish job sources
            DuunitoriSource(),
            JoblySource(),
        ]

        self.latest_jobs = []

    # =========================================================
    # Public search method
    # =========================================================

    def search_jobs(self):
        """
        Search all configured real job sources.

        A failure in one source does not stop the other sources.

        Returns:
            list: Unique real job objects.
        """

        jobs = []

        # Separate duplicate registries.
        seen_urls = set()
        seen_source_ids = set()
        seen_fingerprints = set()

        for searcher in self.searchers:

            source_name = searcher.__class__.__name__

            try:
                results = searcher.search()

                if results is None:
                    results = []

                print(
                    f"{source_name} found "
                    f"{len(results)} jobs"
                )

                for job in results:

                    if job is None:
                        continue

                    # -------------------------------------------------
                    # Read common job fields safely.
                    # -------------------------------------------------

                    title = self._clean_value(
                        self._get_value(job, "title")
                    )

                    company = self._clean_value(
                        self._get_value(job, "company")
                    )

                    location = self._clean_value(
                        self._get_value(job, "location")
                    )

                    url = self._clean_url(
                        self._get_value(job, "url")
                    )

                    source = self._clean_value(
                        self._get_value(job, "source")
                    )

                    source_id = self._clean_value(
                        self._get_value(job, "source_id")
                    )

                    description = self._clean_value(
                        self._get_value(job, "description")
                    )

                    # If source object did not provide a source name,
                    # use the actual source class.
                    if not source:
                        source = source_name

                    # -------------------------------------------------
                    # Ignore completely unusable records.
                    # -------------------------------------------------

                    if not title and not url:
                        continue

                    # -------------------------------------------------
                    # Duplicate check #1:
                    # source + source-specific ID
                    # -------------------------------------------------

                    source_id_key = None

                    if source_id:
                        source_id_key = (
                            source.lower(),
                            source_id.lower(),
                        )

                        if source_id_key in seen_source_ids:
                            continue

                    # -------------------------------------------------
                    # Duplicate check #2:
                    # canonical URL
                    # -------------------------------------------------

                    url_key = None

                    if url:
                        url_key = self._canonical_url(url)

                        if url_key in seen_urls:
                            continue

                    # -------------------------------------------------
                    # Duplicate check #3:
                    # content fingerprint
                    #
                    # Important:
                    # We do NOT use only:
                    #
                    # title + company + location
                    #
                    # because a company can legitimately have multiple
                    # jobs with the same title and location.
                    #
                    # Description is therefore included.
                    # -------------------------------------------------

                    fingerprint = self._job_fingerprint(
                        title=title,
                        company=company,
                        location=location,
                        description=description,
                    )

                    if fingerprint in seen_fingerprints:
                        continue

                    # -------------------------------------------------
                    # Register duplicate keys.
                    # -------------------------------------------------

                    if source_id_key is not None:
                        seen_source_ids.add(
                            source_id_key
                        )

                    if url_key:
                        seen_urls.add(
                            url_key
                        )

                    seen_fingerprints.add(
                        fingerprint
                    )

                    # -------------------------------------------------
                    # Assign local CareerPilot ID.
                    # -------------------------------------------------

                    self._set_job_id(
                        job,
                        len(jobs),
                    )

                    # -------------------------------------------------
                    # Make sure source information exists.
                    # -------------------------------------------------

                    existing_source = self._get_value(
                        job,
                        "source",
                    )

                    if not existing_source:
                        self._set_job_value(
                            job,
                            "source",
                            source,
                        )

                    jobs.append(job)

            except Exception as error:

                print(
                    f"{source_name} failed: {error}"
                )

                # Continue with the remaining real sources.
                continue

        # ---------------------------------------------------------
        # Store latest results for the application.
        # ---------------------------------------------------------

        self.latest_jobs = jobs

        print(
            f"Collected {len(jobs)} unique jobs"
        )

        return jobs

    # =========================================================
    # Job lookup
    # =========================================================

    def get_job(self, job_id):
        """
        Return a job from the latest search results.

        Args:
            job_id: CareerPilot local job ID.

        Returns:
            Job object/dictionary or None.
        """

        try:
            job_id = int(job_id)
        except (TypeError, ValueError):
            return None

        if job_id < 0:
            return None

        if job_id >= len(self.latest_jobs):
            return None

        return self.latest_jobs[job_id]

    # =========================================================
    # Duplicate fingerprint
    # =========================================================

    def _job_fingerprint(
        self,
        title,
        company,
        location,
        description,
    ):
        """
        Build a conservative fingerprint for duplicate detection.

        The description is included so that two legitimate jobs
        having the same title/company/location are not automatically
        treated as duplicates.
        """

        title = self._normalise_text(title)
        company = self._normalise_text(company)
        location = self._normalise_text(location)
        description = self._normalise_text(description)

        # Use enough description to distinguish separate postings
        # while avoiding huge fingerprint strings.
        description_part = description[:1500]

        return (
            title,
            company,
            location,
            description_part,
        )

    # =========================================================
    # URL canonicalization
    # =========================================================

    def _canonical_url(self, url):
        """
        Normalize a URL only for duplicate detection.

        The original job.url is never modified.

        Removes:
        - surrounding whitespace
        - trailing slash
        - common tracking parameters
        """

        url = str(url or "").strip()

        if not url:
            return ""

        # Normalize case for duplicate comparison.
        url = url.lower()

        if "?" in url:

            base, query = url.split(
                "?",
                1,
            )

            kept_parameters = []

            ignored_prefixes = (
                "utm_",
                "source=",
                "ref=",
                "referrer=",
                "tracking=",
            )

            for parameter in query.split("&"):

                parameter_lower = parameter.lower()

                if parameter_lower.startswith(
                    ignored_prefixes
                ):
                    continue

                kept_parameters.append(
                    parameter
                )

            if kept_parameters:
                url = (
                    base
                    + "?"
                    + "&".join(kept_parameters)
                )
            else:
                url = base

        return url.rstrip("/")

    # =========================================================
    # Generic object/dictionary access
    # =========================================================

    def _get_value(self, obj, field):
        """
        Read a field from either:
        - a dictionary
        - a normal Python object
        """

        if obj is None:
            return None

        if isinstance(obj, dict):
            return obj.get(field)

        return getattr(
            obj,
            field,
            None,
        )

    def _set_job_value(
        self,
        job,
        field,
        value,
    ):
        """
        Set a field on either a dictionary or an object.
        """

        if isinstance(job, dict):
            job[field] = value
            return

        try:
            setattr(
                job,
                field,
                value,
            )
        except Exception:
            pass

    def _set_job_id(
        self,
        job,
        job_id,
    ):
        """
        Assign CareerPilot's local job ID.

        Supports both dictionaries and normal Job objects.
        """

        self._set_job_value(
            job,
            "id",
            job_id,
        )

    # =========================================================
    # Text cleaning
    # =========================================================

    def _clean_value(self, value):
        """
        Safely convert a source value to a normalized string.
        """

        if value is None:
            return ""

        text = str(value)

        text = (
            text
            .replace("\xa0", " ")
            .replace("\\_", "_")
        )

        return " ".join(
            text.strip().split()
        )

    def _clean_url(self, value):
        """
        Clean a URL for comparison.

        The actual job URL is preserved on the Job object.
        """

        return self._clean_value(value)

    def _normalise_text(self, value):
        """
        Normalize text used for duplicate comparison.
        """

        text = self._clean_value(value)

        return " ".join(
            text.lower().split()
        )