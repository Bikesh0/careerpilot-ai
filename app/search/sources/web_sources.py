import json
import re
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup

from app.models.job import Job


class WebSourceBase:

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/151.0 Safari/537.36"
        )
    }

    TIMEOUT = 20

    RELEVANT_TITLE_PATTERNS = [
        "soc analyst",
        "security analyst",
        "cybersecurity analyst",
        "cyber security analyst",
        "information security analyst",
        "information security specialist",
        "security engineer",
        "cybersecurity engineer",
        "cyber security engineer",
        "security specialist",
        "security operations",
        "security operations analyst",
        "security operations engineer",
        "security administrator",
        "it security",
        "it security specialist",
        "cybersecurity",
        "cyber security",
        "infosec",
        "cloud security",
        "cloud security engineer",
        "network security",
        "network security engineer",
        "iam analyst",
        "iam engineer",
        "identity and access",
        "devsecops",
        "system administrator",
        "systems administrator",
        "linux administrator",
        "linux engineer",
        "network administrator",
        "network engineer",
        "cloud engineer",
        "cloud support",
        "cloud support engineer",
        "devops engineer",
        "infrastructure engineer",
        "technical support engineer",
        "technical support",
        "it support",
        "help desk",
        "helpdesk",
        "service desk",
    ]

    def get_page(self, url):

        try:

            response = requests.get(
                url,
                headers=self.HEADERS,
                timeout=self.TIMEOUT,
            )

            response.raise_for_status()

            return response.text

        except requests.exceptions.SSLError as error:

            print(
                f"[{self.__class__.__name__}] "
                f"TLS verification failed: {error}"
            )

            return None

        except requests.RequestException as error:

            print(
                f"[{self.__class__.__name__}] "
                f"Request failed: {error}"
            )

            return None

    def clean(self, value):

        if not value:
            return ""

        return re.sub(
            r"\s+",
            " ",
            str(value)
        ).strip()

    def title_is_relevant(self, title):

        title = self.clean(title).lower()

        if not title:
            return False

        return any(
            pattern in title
            for pattern in self.RELEVANT_TITLE_PATTERNS
        )

    def make_job(
        self,
        title,
        company,
        location,
        url,
        source,
        description="",
    ):

        title = self.clean(title)
        company = self.clean(company)
        location = self.clean(location)
        url = self.clean(url)
        description = self.clean(description)

        if not title or not url:
            return None

        return Job(
            title=title,
            company=company,
            location=location,
            url=url,
            description=description,
            source=source,
        )


class DuunitoriSource(WebSourceBase):

    SOURCE = "Duunitori"

    BASE_URL = "https://duunitori.fi"

    SEARCH_URL = (
        "https://duunitori.fi/tyopaikat?haku={query}"
    )

    SEARCH_TERMS = [
        "SOC analyst",
        "security analyst",
        "cybersecurity",
        "cyber security",
        "information security",
        "security engineer",
        "security specialist",
        "cloud security",
        "network security",
        "devsecops",
        "linux administrator",
        "system administrator",
        "cloud engineer",
        "devops engineer",
        "technical support",
    ]

    def search(self):

        jobs = []

        seen = set()

        for query in self.SEARCH_TERMS:

            try:

                url = self.SEARCH_URL.format(
                    query=quote(query)
                )

                html = self.get_page(url)

                if not html:
                    continue

                soup = BeautifulSoup(
                    html,
                    "html.parser"
                )

                for link in soup.find_all(
                    "a",
                    href=True
                ):

                    href = link.get(
                        "href",
                        ""
                    )

                    title = self.clean(
                        link.get_text(
                            " ",
                            strip=True
                        )
                    )

                    if "/tyopaikat/tyo/" not in href:
                        continue

                    if not title:
                        continue

                    if not self.title_is_relevant(title):
                        continue

                    full_url = urljoin(
                        self.BASE_URL,
                        href
                    )

                    if "lisaa_suosikkeihin" in (
                        full_url.lower()
                    ):
                        continue

                    key = full_url.lower()

                    if key in seen:
                        continue

                    seen.add(key)

                    detail_html = self.get_page(
                        full_url
                    )

                    if not detail_html:
                        continue

                    details = self.parse_job_detail(
                        detail_html,
                        title
                    )

                    job = self.make_job(
                        title=(
                            details["title"]
                            or title
                        ),
                        company=details["company"],
                        location=details["location"],
                        url=full_url,
                        source=self.SOURCE,
                        description=details["description"],
                    )

                    if job:
                        jobs.append(job)

            except Exception as error:

                print(
                    "Duunitori source error:",
                    error
                )

        print(
            f"DuunitoriSource found "
            f"{len(jobs)} jobs"
        )

        return jobs

    def parse_job_detail(
        self,
        html,
        fallback_title=""
    ):

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        title = ""
        company = ""
        location = ""
        description = ""

        for script in soup.find_all(
            "script",
            type="application/ld+json"
        ):

            try:

                raw = (
                    script.string
                    or script.get_text()
                )

                data = json.loads(raw)

                candidates = []

                if isinstance(data, dict):

                    if "@graph" in data:

                        candidates.extend(
                            data["@graph"]
                        )

                    else:

                        candidates.append(
                            data
                        )

                elif isinstance(data, list):

                    candidates.extend(data)

                for item in candidates:

                    if not isinstance(
                        item,
                        dict
                    ):
                        continue

                    item_type = item.get(
                        "@type",
                        ""
                    )

                    if isinstance(
                        item_type,
                        list
                    ):

                        is_job = (
                            "JobPosting"
                            in item_type
                        )

                    else:

                        is_job = (
                            item_type
                            == "JobPosting"
                        )

                    if not is_job:
                        continue

                    title = self.clean(
                        item.get(
                            "title",
                            ""
                        )
                    )

                    description = self.clean(
                        BeautifulSoup(
                            str(
                                item.get(
                                    "description",
                                    ""
                                )
                            ),
                            "html.parser"
                        ).get_text(
                            " ",
                            strip=True
                        )
                    )

                    organization = item.get(
                        "hiringOrganization",
                        {}
                    )

                    if isinstance(
                        organization,
                        dict
                    ):

                        company = self.clean(
                            organization.get(
                                "name",
                                ""
                            )
                        )

                    job_location = item.get(
                        "jobLocation",
                        {}
                    )

                    if isinstance(
                        job_location,
                        list
                    ):

                        if job_location:

                            job_location = (
                                job_location[0]
                            )

                        else:

                            job_location = {}

                    if isinstance(
                        job_location,
                        dict
                    ):

                        address = job_location.get(
                            "address",
                            {}
                        )

                        if isinstance(
                            address,
                            dict
                        ):

                            parts = []

                            for field in (
                                "addressLocality",
                                "addressRegion",
                                "addressCountry",
                            ):

                                value = self.clean(
                                    address.get(
                                        field,
                                        ""
                                    )
                                )

                                if value:
                                    parts.append(
                                        value
                                    )

                            location = ", ".join(
                                parts
                            )

                    break

            except (
                json.JSONDecodeError,
                TypeError,
                AttributeError
            ):

                continue

        if not title:

            heading = soup.find("h1")

            if heading:

                title = self.clean(
                    heading.get_text(
                        " ",
                        strip=True
                    )
                )

        if not company:

            heading = soup.find("h1")

            if heading:

                parent = heading.parent

                for _ in range(5):

                    if not parent:
                        break

                    links = parent.find_all(
                        "a",
                        href=True
                    )

                    for candidate in links:

                        candidate_text = self.clean(
                            candidate.get_text(
                                " ",
                                strip=True
                            )
                        )

                        if (
                            candidate_text
                            and candidate_text != title
                            and len(candidate_text) < 150
                        ):

                            candidate_href = (
                                candidate.get(
                                    "href",
                                    ""
                                ).lower()
                            )

                            if (
                                "yritys"
                                in candidate_href
                                or
                                "company"
                                in candidate_href
                            ):

                                company = (
                                    candidate_text
                                )

                                break

                    if company:
                        break

                    parent = parent.parent

        if not location:

            text = self.clean(
                soup.get_text(
                    " ",
                    strip=True
                )
            )

            location = self.extract_location(
                text
            )

        if not description:

            candidates = [
                soup.find("main"),
                soup.find("article")
            ]

            for candidate in candidates:

                if not candidate:
                    continue

                text = self.clean(
                    candidate.get_text(
                        " ",
                        strip=True
                    )
                )

                if len(text) > 300:

                    description = text

                    break

        return {
            "title": (
                title
                or fallback_title
            ),
            "company": company,
            "location": location,
            "description": description,
        }

    def extract_location(self, text):

        cities = [
            "Helsinki",
            "Espoo",
            "Vantaa",
            "Tampere",
            "Turku",
            "Oulu",
            "JyvÃ¤skylÃ¤",
            "Lahti",
            "Kuopio",
            "Vaasa",
            "Finland",
            "Suomi",
        ]

        text_lower = text.lower()

        for city in cities:

            if city.lower() in text_lower:

                return city

        return "Finland"


class JoblySource(WebSourceBase):

    SOURCE = "Jobly"

    BASE_URL = "https://www.jobly.fi"

    SEARCH_URL = (
        "https://www.jobly.fi/tyopaikat?search={query}"
    )

    SEARCH_TERMS = [
        "SOC analyst",
        "security analyst",
        "kyberturvallisuus",
        "cybersecurity",
        "information security",
        "security engineer",
        "security specialist",
        "cloud security",
        "network security",
        "system administrator",
        "linux administrator",
        "cloud engineer",
        "devops",
        "technical support",
    ]

    def search(self):

        jobs = []

        seen = set()

        for query in self.SEARCH_TERMS:

            try:

                url = self.SEARCH_URL.format(
                    query=quote(query)
                )

                html = self.get_page(url)

                if not html:
                    continue

                soup = BeautifulSoup(
                    html,
                    "html.parser"
                )

                for link in soup.find_all(
                    "a",
                    href=True
                ):

                    href = link.get(
                        "href",
                        ""
                    )

                    title = self.clean(
                        link.get_text(
                            " ",
                            strip=True
                        )
                    )

                    if (
                        "/tyopaikat/" not in href
                        and "/tyopaikka/" not in href
                    ):
                        continue

                    if not title:
                        continue

                    if len(title) < 4:
                        continue

                    if title.lower() in [
                        "tallenna tyÃ¶paikka",
                        "tallenna haku"
                    ]:
                        continue

                    if not self.title_is_relevant(
                        title
                    ):
                        continue

                    full_url = urljoin(
                        self.BASE_URL,
                        href
                    )

                    key = full_url.lower()

                    if key in seen:
                        continue

                    seen.add(key)

                    detail_html = self.get_page(
                        full_url
                    )

                    if detail_html:

                        details = (
                            self.parse_job_detail(
                                detail_html,
                                title
                            )
                        )

                    else:

                        details = {
                            "title": title,
                            "company": "",
                            "location": "Finland",
                            "description": "",
                        }

                    job = self.make_job(
                        title=(
                            details["title"]
                            or title
                        ),
                        company=details["company"],
                        location=details["location"],
                        url=full_url,
                        source=self.SOURCE,
                        description=details["description"],
                    )

                    if job:
                        jobs.append(job)

            except Exception as error:

                print(
                    "Jobly source error:",
                    error
                )

        print(
            f"JoblySource found "
            f"{len(jobs)} jobs"
        )

        return jobs

    def parse_job_detail(
        self,
        html,
        fallback_title=""
    ):

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        title = ""
        company = ""
        location = ""
        description = ""

        for script in soup.find_all(
            "script",
            type="application/ld+json"
        ):

            try:

                raw = (
                    script.string
                    or script.get_text()
                )

                data = json.loads(raw)

                candidates = []

                if isinstance(data, dict):

                    if "@graph" in data:

                        candidates.extend(
                            data["@graph"]
                        )

                    else:

                        candidates.append(
                            data
                        )

                elif isinstance(data, list):

                    candidates.extend(data)

                for item in candidates:

                    if not isinstance(
                        item,
                        dict
                    ):
                        continue

                    item_type = item.get(
                        "@type",
                        ""
                    )

                    if isinstance(
                        item_type,
                        list
                    ):

                        is_job = (
                            "JobPosting"
                            in item_type
                        )

                    else:

                        is_job = (
                            item_type
                            == "JobPosting"
                        )

                    if not is_job:
                        continue

                    title = self.clean(
                        item.get(
                            "title",
                            ""
                        )
                    )

                    description = self.clean(
                        BeautifulSoup(
                            str(
                                item.get(
                                    "description",
                                    ""
                                )
                            ),
                            "html.parser"
                        ).get_text(
                            " ",
                            strip=True
                        )
                    )

                    organization = item.get(
                        "hiringOrganization",
                        {}
                    )

                    if isinstance(
                        organization,
                        dict
                    ):

                        company = self.clean(
                            organization.get(
                                "name",
                                ""
                            )
                        )

                    job_location = item.get(
                        "jobLocation",
                        {}
                    )

                    if isinstance(
                        job_location,
                        list
                    ):

                        if job_location:

                            job_location = (
                                job_location[0]
                            )

                        else:

                            job_location = {}

                    if isinstance(
                        job_location,
                        dict
                    ):

                        address = job_location.get(
                            "address",
                            {}
                        )

                        if isinstance(
                            address,
                            dict
                        ):

                            parts = []

                            for field in (
                                "addressLocality",
                                "addressRegion",
                                "addressCountry",
                            ):

                                value = self.clean(
                                    address.get(
                                        field,
                                        ""
                                    )
                                )

                                if value:
                                    parts.append(
                                        value
                                    )

                            location = ", ".join(
                                parts
                            )

                    break

            except (
                json.JSONDecodeError,
                TypeError,
                AttributeError
            ):

                continue

        if not title:

            heading = soup.find("h1")

            if heading:

                title = self.clean(
                    heading.get_text(
                        " ",
                        strip=True
                    )
                )

        if not location:

            text = self.clean(
                soup.get_text(
                    " ",
                    strip=True
                )
            )

            location = self.extract_location(
                text
            )

        if not description:

            candidates = [
                soup.find("main"),
                soup.find("article")
            ]

            for candidate in candidates:

                if not candidate:
                    continue

                text = self.clean(
                    candidate.get_text(
                        " ",
                        strip=True
                    )
                )

                if len(text) > 300:

                    description = text

                    break

        return {
            "title": (
                title
                or fallback_title
            ),
            "company": company,
            "location": location,
            "description": description,
        }

    def extract_location(self, text):

        cities = [
            "Helsinki",
            "Espoo",
            "Vantaa",
            "Tampere",
            "Turku",
            "Oulu",
            "JyvÃ¤skylÃ¤",
            "Lahti",
            "Kuopio",
            "Vaasa",
            "Finland",
            "Suomi",
        ]

        text_lower = text.lower()

        for city in cities:

            if city.lower() in text_lower:

                return city

        return "Finland"
class TyomarkkinatoriSource(WebSourceBase):

    SOURCE = "Tyomarkkinatori"
    BASE_URL = "https://tyomarkkinatori.fi"

    SEARCH_TERMS = [
        "SOC analyst",
        "security analyst",
        "kyberturvallisuus",
        "tietoturva",
        "information security",
        "security engineer",
        "security specialist",
        "cloud security",
        "network security",
        "jarjestelmaasiantuntija",
        "system administrator",
        "cloud engineer",
        "devops",
        "technical support",
    ]

    SEARCH_URL = (
        "https://tyomarkkinatori.fi/henkiloasiakkaat/avoimet-tyopaikat"
    )

    def search(self):

        jobs = []
        seen = set()

        html = self.get_page(self.SEARCH_URL)

        if not html:
            return jobs

        soup = BeautifulSoup(html, "html.parser")

        for link in soup.find_all("a", href=True):

            href = link.get("href", "")
            title = self.clean(
                link.get_text(" ", strip=True)
            )

            if not title or len(title) < 4:
                continue

            if not self.title_is_relevant(title):
                continue

            full_url = urljoin(self.BASE_URL, href)
            key = full_url.lower()

            if key in seen:
                continue

            seen.add(key)

            job = self.make_job(
                title=title,
                company="",
                location="Finland",
                url=full_url,
                source=self.SOURCE,
                description="",
            )

            if job:
                jobs.append(job)

        print(
            f"TyomarkkinatoriSource found "
            f"{len(jobs)} jobs"
        )

        return jobs


class WorkInFinlandSource(WebSourceBase):

    SOURCE = "Work in Finland"
    BASE_URL = "https://www.workinfinland.com"

    SEARCH_URL = (
        "https://www.workinfinland.com/en/open-jobs/"
    )

    SEARCH_TERMS = [
        "security",
        "cybersecurity",
        "information security",
        "security engineer",
        "security analyst",
        "cloud security",
        "network security",
        "devops",
        "cloud engineer",
        "software engineer",
        "technical support",
        "system administrator",
    ]

    def search(self):

        jobs = []
        seen = set()

        html = self.get_page(self.SEARCH_URL)

        if not html:
            return jobs

        soup = BeautifulSoup(html, "html.parser")

        for link in soup.find_all("a", href=True):

            href = link.get("href", "")
            title = self.clean(
                link.get_text(" ", strip=True)
            )

            if not title or len(title) < 4:
                continue

            if not self.title_is_relevant(title):
                continue

            full_url = urljoin(self.BASE_URL, href)
            key = full_url.lower()

            if key in seen:
                continue

            seen.add(key)

            job = self.make_job(
                title=title,
                company="",
                location="Finland",
                url=full_url,
                source=self.SOURCE,
                description="",
            )

            if job:
                jobs.append(job)

        print(
            f"WorkInFinlandSource found "
            f"{len(jobs)} jobs"
        )

        return jobs

