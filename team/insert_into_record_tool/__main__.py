"""Update one metric in an explicitly selected JSON record."""

import argparse
import json
from pathlib import Path

from . import update_record_file


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path, help="JSON record to update")
    parser.add_argument("metric", help="Existing metric name, for example F1")
    parser.add_argument("value", type=float, help="New numeric metric value")
    args = parser.parse_args()

    record = update_record_file(args.record, args.metric, args.value)
    print(json.dumps(record.record, indent=2))


if __name__ == "__main__":
    main()
