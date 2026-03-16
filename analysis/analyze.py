#!/usr/bin/env python3 

import pathlib
import json
import sys

job_id = sys.argv[1]
print(list(pathlib.Path('data').glob(f"{job_id}-*.json")))

for f in pathlib.Path('data').glob(f"{job_id}-*.json"):
    result = json.load(f.open())
    for rec in result['result']['records']:
        print(rec['status'], rec['url'])
