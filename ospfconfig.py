#!/usr/bin/env python3
from flask import Blueprint, request, render_template
from napalm import get_network_driver
from ssh_info import load_ssh_info
import sqlite3
from prettytable import PrettyTable
import ipaddress
import csv

ospf_blueprint = Blueprint("ospf", __name__)
routers = load_ssh_info()

#create db if it is not exist
def create_database():
    with sqlite3.connect("ospf_config.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ospf_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                router TEXT NOT NULL,
                ospf_process_id INTEGER NOT NULL,
                router_id TEXT NOT NULL,
                primary_network TEXT NOT NULL,
                primary_area INTEGER NOT NULL,
                secondary_network TEXT,
                secondary_area INTEGER,
                enable_ecmp INTEGER DEFAULT 0,
                username TEXT NOT NULL
            )
        ''')
        conn.commit()

create_database()

def check_wrong_ips(file_path="wrong_ips.csv"):
    try:
        with open(file_path, mode="r", encoding="utf8") as file:
            reader = csv.reader(file)
            return {row[0] for row in reader}
    except FileNotFoundError:
        return set()

def validate_ip(ip):
    wrong_ips = check_wrong_ips()
    if ip in wrong_ips:
        return False
    try:
        ipaddress.ip_address(str(ip))
        return True
    except ValueError:
        return False

@ospf_blueprint.route("/ospfconfig", methods=["GET", "POST"])
def ospf_config():
    if request.method == "GET":
        return render_template("ospf.html", show_form=True)

    if request.method == "POST":
        router = request.form["router"]
        if router not in routers:
            return "Error: Router not found"

        username = request.form["username"]
        password = request.form["password"]
        ospf_process_id = request.form["ospf_process_id"]
        loopback_ip = request.form["loopback_ip"]
        primary_network = request.form["ospf_network_1"]
        primary_area = request.form["ospf_area_1"]

        secondary_network = request.form.get("ospf_network_2")
        secondary_area = request.form.get("ospf_area_2")
        enable_ecmp = 1 if "enable_ecmp" in request.form else 0

        
        #checking correct ip address 
        try:
            ipaddress.IPv4Network(primary_network, strict=False)  # strict=False позволяет вводить без маски
        except ValueError:
            return f"Error: Invalid primary network {primary_network}. Please enter a valid network"

        if not validate_ip(loopback_ip):
            return f"Error: Invalid loopback IP {loopback_ip}. Please enter a valid IP."
        if secondary_network:
            try:
                ipaddress.IPv4Network(secondary_network, strict=False)
            except ValueError:
                return f"Error: Invalid secondary network {secondary_network}. Please enter a valid network."

        # checking secondary network for R2 and R4
        if router in ["R2", "R4"]:
            secondary_network = request.form.get("ospf_network_2", None)
            secondary_area = request.form.get("ospf_area_2", None)

            if secondary_network and not validate_ip(secondary_network):
                return f"Error: Invalid secondary network {secondary_network}. Please enter a valid IP."


        #save detail on database
        with sqlite3.connect("ospf_config.db") as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ospf_configs (router, ospf_process_id, router_id, primary_network, primary_area,
                                          secondary_network, secondary_area, enable_ecmp, username)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (router, ospf_process_id, loopback_ip, primary_network, primary_area,
                  secondary_network, secondary_area, enable_ecmp, username))
            conn.commit()

        # Connect to router
        router_ip = routers[router]["ip"]
        driver = get_network_driver("ios")
        device = driver(router_ip, username, password, optional_args={"use_scp": False})
        device.open()

        #deploy into OSPF 
        ospf_config = f"""
        router ospf {ospf_process_id}
          router-id {loopback_ip}
          network {primary_network} 0.0.0.255 area {primary_area}
          network {loopback_ip} 0.0.0.0 area {primary_area}
        """
        if secondary_network and secondary_area:
            ospf_config += f"  network {secondary_network} 0.0.0.255 area {secondary_area}\n"
        
        # **Если маршрутизатор R2 или R4, он становится ABR и добавляет inter-area конфигурацию**
        if router in ["R2", "R4"] and primary_area != secondary_area:
            ospf_config += f"  area {primary_area} range {primary_network} 255.255.255.0\n"
            ospf_config += f"  area {secondary_area} range {secondary_network} 255.255.255.0\n"
            ospf_config += "  redistribute connected subnets\n"
        if enable_ecmp:
            ospf_config += "  maximum-paths 2\n"

        #apply all configis
        device.load_merge_candidate(config=ospf_config)
        diff = device.compare_config()
        if not diff:
            device.discard_config()
            return render_template("ospf.html", show_form=False, ospf_output="No changes applied", ospf_table=None)

        device.commit_config()

        #extract data from sqlite3
        with sqlite3.connect("ospf_config.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT router, ospf_process_id, router_id, primary_network, primary_area, secondary_network, secondary_area FROM ospf_configs")
            rows = cursor.fetchall()

        
        #Output
        ospf_table = PrettyTable(["Router", "OSPF Process", "Router ID", "Primary Network", "Primary Area", "Secondary Network", "Secondary Area"])
        for row in rows:
            ospf_table.add_row(row)

        return render_template("ospf.html", show_form=False, ospf_output="OSPF Configuration Applied Successfully", ospf_table=ospf_table)
