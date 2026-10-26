
from backend.db import (
    get_universities,
    get_programs,
    get_tuition,
    get_intakes,
)

print("\nDATABASE CONNECTION TEST")

print("\nUniversities:")
for item in get_universities():
    print(item)

print("\nGachon Programs:")
for item in get_programs("Gachon University"):
    print(item)

print("\nGachon Tuition:")
for item in get_tuition("Gachon University"):
    print(item)

print("\nGachon Intakes:")
for item in get_intakes("Gachon University"):
    print(item)

print("\nPostgreSQL connection successful!")
