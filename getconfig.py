#/usr/bin/env python3


from napalm import get_network_driver
from flask import render_template
import datetime
from ssh_info import load_ssh_info

#load device credentials from sshInfo file
routers = load_ssh_info()

def get_router_configs():
    driver = get_network_driver("ios")
    config_files = []

    for name, details in routers.items():
        device = driver(details["ip"], details["username"], details["password"])
        device.open()
        config = device.get_config()['running']
        
        timestamp = datetime.datetime.now().isoformat()
        filename = f"{name}_{timestamp}.txt"
        
        with open(filename, "w") as f:
            f.write(config)
        
        config_files.append(filename)
        device.close()

    return render_template('saved_configs.html', files=config_files)
