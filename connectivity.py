#/usr/bin/env python3

import csv
import subprocess

file_path = 'sshInfo.csv'

def connectivity():
    with open(file_path, mode='r', encoding='utf8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            ip = row.get('ip')
            host = row.get('hostname')
            if not ip:
                print("host row is empty")
                continue
            if ip:
                print(f"pinging {host}")
                result = subprocess.run(["ping", "-c", "2", ip], capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"{host} is reachable")
                else:
                    print(f"{host} is not pinging")

connectivity()