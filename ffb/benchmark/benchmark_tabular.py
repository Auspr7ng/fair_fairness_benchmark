"""Dispatch to an implemented tabular trainer instead of the legacy stub.

Use --dry-run to inspect the command without loading training dependencies.
Unknown options are forwarded to the selected trainer, which validates them.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def build_command(args, extra):
    source = Path(__file__).resolve().parents[1] / 'src'
    dataset = 'kdd' if args.dataset_name == 'census_income_kdd' else args.dataset_name
    command = [sys.executable, str(source / f'ffb_tabular_{args.method}.py'),
               '--dataset', dataset, '--data_path', args.dataset_path,
               '--sensitive_attr', args.sensitive_attr, '--target_attr', args.target_attr]
    return command + extra, source


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset_path', required=True)
    parser.add_argument('--dataset_name', default='adult',
                        choices=['adult', 'german', 'bank_marketing', 'compas', 'acs', 'kdd', 'census_income_kdd'])
    parser.add_argument('--sensitive_attr', default='sex')
    parser.add_argument('--target_attr', default='income')
    parser.add_argument('--method', '--deiasing_method', dest='method', choices=['erm', 'diffdp'], default='diffdp')
    parser.add_argument('--dry-run', action='store_true')
    args, extra = parser.parse_known_args(argv)
    command, cwd = build_command(args, extra)
    if args.dry_run:
        print(json.dumps({'command': command, 'cwd': str(cwd)}))
        return 0
    return subprocess.run(command, cwd=cwd).returncode


if __name__ == '__main__':
    raise SystemExit(main())
