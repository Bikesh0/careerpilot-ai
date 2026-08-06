from dataclasses import dataclass


@dataclass
class Application:

    id: int | None = None

    company: str = ""

    title: str = ""

    location: str = ""

    source: str = ""

    status: str = "Saved"

    applied_date: str = ""

    resume_file: str = ""

    cover_letter_file: str = ""

    notes: str = ""