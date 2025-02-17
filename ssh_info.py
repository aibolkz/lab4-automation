#/usr/bin/env python3
import csv

def load_ssh_info(csv_file="sshInfo.csv"):
    routers = {}
    with open(csv_file, mode="r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            routers[row["hostname"]] = {
                "ip": row["ip"],
                "username": row["username"],
                "password": row["password"]
            }
    return routers
