#!/usr/bin/env python3
from flask import Blueprint, render_template
from napalm import get_network_driver
from ssh_info import load_ssh_info

migration_blueprint = Blueprint("migration", __name__)

#load router credentials
routers = load_ssh_info()
r4_info = routers.get("R4")

def migrate_r4():
    """Perform the migration process for R4"""
    steps = []

    if not r4_info:
        steps.append("Error: R4 credentials not found.")
        return render_template("migration.html", steps=steps)

    driver = get_network_driver("ios")
    device = driver(r4_info["ip"], r4_info["username"], r4_info["password"])



    try:
        device.open()
        steps.append("Connected to R4 successfully.")



        #set Fa0/0 as passive-interface
        ospf_config = "router ospf 1\n passive-interface FastEthernet0/0"
        device.load_merge_candidate(config=ospf_config)
        device.commit_config()
        steps.append("Set Fa0/0 as passive-interface.")



        #test connectivity before shutdown
        ping_result = device.ping("30.0.0.1")
        ping_status = "Success" if ping_result.get("success", 0) else "Failed"
        steps.append(f"Ping test to R3 before migration: {ping_status}")



        #shutdown Fa0/0
        shutdown_config = "interface FastEthernet0/0\n shutdown"
        device.load_merge_candidate(config=shutdown_config)
        device.commit_config()
        steps.append("Shut down Fa0/0 on R4.")



        # Test connection 
        ping_result_after = device.ping("30.0.0.1")
        ping_status_after = "Success" if ping_result_after.get("success", 0) else "Failed"
        steps.append(f"Ping test to R3 after shutting down Fa0/0: {ping_status_after}")



        #bring Fa0/0 back up
        no_shutdown_config = "interface FastEthernet0/0\n no shutdown"
        device.load_merge_candidate(config=no_shutdown_config)
        device.commit_config()
        steps.append("Brought Fa0/0 back up.")



        #migration banner
        banner_config = "banner motd ^C Change made for migration in Lab 6 ^C"
        device.load_merge_candidate(config=banner_config)
        device.commit_config()
        steps.append("Migration banner applied.")



        #remove passive-interface Fa0/0
        remove_passive_config = "router ospf 1\n no passive-interface FastEthernet0/0"
        device.load_merge_candidate(config=remove_passive_config)
        device.commit_config()
        steps.append("Removed passive-interface Fa0/0.")

        steps.append("Migration completed successfully.")

    except Exception as e:
        steps.append(f"Error: {e}")

    finally:
        device.close()

    return render_template("migration.html", steps=steps)

@migration_blueprint.route("/migration")
def migration_page():
    return migrate_r4()
