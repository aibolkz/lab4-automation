#!/usr/bin/env python3
from flask import Blueprint, request, render_template
from napalm import get_network_driver
from ssh_info import load_ssh_info  # Import function

ospf_blueprint = Blueprint("ospf", __name__)

#router credentials from sshInfo.csv
routers = load_ssh_info()

@ospf_blueprint.route("/ospfconfig", methods=["GET", "POST"])
def ospf_config():
    """OSPF Configuration Page"""
    if request.method == "GET":
        return render_template("ospf.html")  # Load the form

    if request.method == "POST":
        # Process the form submission
        router = request.form["router"]
        if router not in routers:
            return f"Error: Router {router} is not defined in sshInfo.csv."

        username = request.form["username"]
        password = request.form["password"]
        ospf_process_id = request.form["ospf_process_id"]
        loopback_ip = request.form["loopback_ip"]
        primary_network = request.form["ospf_network_1"]
        primary_area = request.form["ospf_area_1"]

        #fields for R2 and R4
        secondary_network = request.form.get("ospf_network_2", None)
        secondary_area = request.form.get("ospf_area_2", None)
        enable_ecmp = "enable_ecmp" in request.form

        #router details
        router_ip = routers[router]["ip"]
        driver = get_network_driver("ios")
        device = driver(router_ip, username, password, optional_args={"use_scp": False})
        device.open()

        # Build OSPF configuration
        ospf_config = f"""
        router ospf {ospf_process_id}
          router-id {loopback_ip}
          network {primary_network} 0.0.0.255 area {primary_area}
          network {loopback_ip} 0.0.0.0 area {primary_area}
        """
        if secondary_network and secondary_area:
            ospf_config += f"""  network {secondary_network} 0.0.0.255 area {secondary_area}
            """
        if enable_ecmp:
            ospf_config += "  maximum-paths 2\n"

        #applying config
        device.load_merge_candidate(config=ospf_config)
        device.commit_config()

        ospf_output = device.cli(["show ip ospf interface brief"])
        # Return the OSPF output as response
        return f"""<h2>OSPF Configuration Applied to {router}</h2><pre>{ospf_output['show ip ospf interface brief']}</pre>  <br>
             <form action="/ospfconfig" method="get"><button type="submit">Back to Configuration</button></form>"""
        device.close()

        return f"OSPF configuration applied to {router}."
