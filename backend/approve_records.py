
from pathlib import Path

FOLDER = Path("data/report_topics_staging")

# Add ONLY record filenames you have checked and approved.
APPROVED_FILES = {
    "d2_spring_intake.txt",
    # "d2_fall_intake.txt",
    # "d4_march_intake.txt",
}


def approve_file(path):
    text = path.read_text(encoding="utf-8-sig")

    if "REVIEW_STATUS:" not in text:
        raise ValueError(f"Missing REVIEW_STATUS: {path}")

    if "PUBLICATION_STATUS:" not in text:
        raise ValueError(f"Missing PUBLICATION_STATUS: {path}")

    lines = text.splitlines()

    updated = []

    for line in lines:
        if line.startswith("REVIEW_STATUS:"):
            line = "REVIEW_STATUS: verified"

        elif line.startswith("PUBLICATION_STATUS:"):
            line = "PUBLICATION_STATUS: approved"

        updated.append(line)

    path.write_text(
        "\n".join(updated) + "\n",
        encoding="utf-8"
    )

    print("Approved:", path)


def main():
    for name in APPROVED_FILES:
        matches = list(FOLDER.rglob(name))

        if len(matches) != 1:
            raise RuntimeError(
                f"Expected one match for {name}, found {len(matches)}"
            )

        approve_file(matches[0])


if __name__ == "__main__":
    main()
