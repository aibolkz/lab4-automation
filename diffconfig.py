#!/usr/bin/env python3
from flask import Blueprint, render_template
import os
import difflib
import glob
import datetime
from napalm import get_network_driver
from ssh_info import load_ssh_info

diff_blueprint = Blueprint("diffconfig", __name__)

CONFIG_DIR = "."  # Config directory
routers = load_ssh_info()  # Load router details


def get_sorted_config_files(router_name):
    """Finds all config files for a router and sorts them by time"""
    files = sorted(
        glob.glob(os.path.join(CONFIG_DIR, f"{router_name}_*.txt")),
        key=os.path.getctime
    )
    return files


def fetch_current_config(router_name, router_details):
    """Fetches and saves current config"""
    driver = get_network_driver("ios")
    device = driver(router_details["ip"], router_details["username"], router_details["password"])
    device.open()
    config = device.get_config()['running']
    device.close()

    # Save new config
    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    new_filename = os.path.join(CONFIG_DIR, f"{router_name}_{timestamp}.txt")

    with open(new_filename, "w") as f:
        f.write(config)

    return new_filename


def compare_configs():
    """Creates new config, compares with first saved config"""
    diffs = {}

    for router, details in routers.items():
        config_files = get_sorted_config_files(router)

        # If no previous configs, just save the new one
        if not config_files:
            new_file = fetch_current_config(router, details)
            diffs[router] = f"Saved first config: {os.path.basename(new_file)}. No previous configs to compare."
            continue

        first_config_file = config_files[0]  # First saved config
        new_config_file = fetch_current_config(router, details)  # Get new config

        with open(first_config_file, "r") as f1, open(new_config_file, "r") as f2:
            first_config = f1.readlines()
            new_config = f2.readlines()

        diff = list(difflib.unified_diff(
            first_config, new_config, fromfile=os.path.basename(first_config_file),
            tofile=os.path.basename(new_config_file), lineterm=""
        ))

        diffs[router] = "\n".join(diff) if diff else "No changes detected"

    return diffs


@diff_blueprint.route("/diffconfig")
def show_diff():
    """Displays config differences"""
    diffs = compare_configs()
    return render_template("diffconfig.html", diffs=diffs)
