"""Compare regenerated FSO numerical results against reference CSV tables."""

import argparse
import csv
import math
from pathlib import Path

RTOL = 1e-8
ATOL = 1e-9

EXACT_FIELDS = {
    "seed", "n", "samples", "successes", "finite_states"
}

def equal_value(expected, actual, field):

    if expected == actual:
        return True

    try:
        x = float(expected)
        y = float(actual)
    except ValueError:
        return False

    if math.isnan(x) or math.isnan(y):
        return math.isnan(x) and math.isnan(y)

    if field.lower() in EXACT_FIELDS:
        return x == y

    return math.isclose(
        x, y, rel_tol=RTOL, abs_tol=ATOL
    )


def read_csv(path):

    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    if not rows:
        raise ValueError(f"Empty CSV: {path}")

    header, data = rows[0], rows[1:]

    if len(header) != len(set(header)):
        raise ValueError(f"Duplicate columns: {path}")

    if any(len(row) != len(header) for row in data):
        raise ValueError(f"Malformed CSV rows: {path}")

    return header, data


def compare(reference, generated):

    expected_files = {
        p.name for p in reference.glob("*.csv")
    }

    actual_files = {
        p.name for p in generated.glob("*.csv")
    }

    if expected_files != actual_files:
        raise AssertionError(
            f"Missing: {expected_files - actual_files}; "
            f"Unexpected: {actual_files - expected_files}"
        )

    if len(expected_files) != 11:
        raise AssertionError(
            f"Expected 11 tables, found {len(expected_files)}"
        )

    failures = []
    total_rows = 0
    total_cells = 0

    for name in sorted(expected_files):

        header1, rows1 = read_csv(reference / name)
        header2, rows2 = read_csv(generated / name)

        if header1 != header2:
            failures.append(f"{name}: column mismatch")
            continue

        if len(rows1) != len(rows2):
            failures.append(f"{name}: row count mismatch")
            continue

        file_failures = 0

        for index, (row1, row2) in enumerate(
            zip(rows1, rows2), start=2
        ):
            total_rows += 1

            for field, expected, actual in zip(
                header1, row1, row2
            ):

                if field == "elapsed_seconds":
                    continue

                total_cells += 1

                if not equal_value(expected, actual, field):
                    failures.append(
                        f"{name}, row {index}, {field}: "
                        f"expected {expected}, obtained {actual}"
                    )
                    file_failures += 1

        status = "PASS" if file_failures == 0 else "FAIL"

        print(
            f"{status}: {name} ({len(rows1)} rows)"
        )

    print("\nVerification summary")
    print("Tables:", len(expected_files))
    print("Rows compared:", total_rows)
    print("Cells compared:", total_cells)
    print("Discrepancies:", len(failures))

    if failures:
        for failure in failures[:20]:
            print(failure)

        raise SystemExit("NUMERICAL REGRESSION FAILED")

    print("ALL NUMERICAL REGRESSION CHECKS PASSED")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "reference", type=Path
    )

    parser.add_argument(
        "generated", type=Path
    )

    args = parser.parse_args()

    compare(args.reference, args.generated)
