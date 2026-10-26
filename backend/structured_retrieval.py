
import json
from decimal import Decimal
from datetime import date, datetime

from backend.db import (
    get_programs,
    get_tuition,
    get_intakes,
)


def format_database_records(records):
    """Convert PostgreSQL records into LLM-readable text."""
    return json.dumps(
        records,
        indent=2,
        default=lambda obj: (
            float(obj)
            if isinstance(obj, Decimal)
            else obj.isoformat()
            if isinstance(obj, (date, datetime))
            else str(obj)
        ),
    )


def retrieve_structured_context(
    question: str,
    university_name: str
) -> str:
    """
    Retrieve structured facts for a known university.
    The university must be resolved before calling this.
    """
    q = question.lower()
    records = []
    category = None

    if any(word in q for word in [
        "tuition", "fee", "cost"
    ]):
        records = get_tuition(university_name)
        category = "tuition"

    elif any(word in q for word in [
        "deadline", "intake", "application date"
    ]):
        records = get_intakes(university_name)
        category = "admissions"

    elif any(word in q for word in [
        "program", "course", "degree", "major"
    ]):
        records = get_programs(university_name)
        category = "programs"

    if not records:
        return ""

    return (
        f"Structured PostgreSQL records ({category}) "
        f"for {university_name}:\n"
        f"{format_database_records(records)}"
    )
