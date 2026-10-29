"""Reviewed snapshots must be rebuilt as a whole to retire stale point IDs."""
import sys


def main():
    print("Single-file upserts are disabled for reviewed snapshots.\n"
          "Run: python backend/review_knowledge.py\n"
          "Then: python backend/index_knowledge.py\n"
          "The indexer verifies a fresh collection before switching the live alias.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
