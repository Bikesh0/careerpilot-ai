from dataclasses import dataclass


@dataclass
class Application:

    company: str
    title: str
    location: str
    source: str

    status: str

    applied_date: str

    resume_file: str = ""

    cover_letter_file: str = ""

    notes: str = ""