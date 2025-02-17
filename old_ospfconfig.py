#/usr/bin/env python3
from napalm import get_network_driver
from ssh_info import load_ssh_info

#load device credentials from file
routers = load_ssh_info()

# OSPF preconfigurations (router-id, network, areas)
ospf_data = {
    "R1": {"router_id": "10.0.0.1", "networks": [("192.51.101.0", "1"), ("10.0.0.1", "1")]},
    "R2": {"router_id": "20.0.0.1", "networks": [("192.51.101.0", "1"), ("20.0.0.1", "1"), ("172.16.1.0", "0")]},
    "R3": {"router_id": "30.0.0.1", "networks": [("172.16.1.0", "0"), ("30.0.0.1", "0")]},
    "R4": {"router_id": "40.0.0.1", "networks": [("192.51.101.0", "1"), ("40.0.0.1", "1"), ("172.16.1.0", "0")]},
}



# for configure OSPF routing
def to_configure_ospf(router):
    if router not in routers:
        return f"!!! Error: Router {router} not found in sshInfo.csv"
    details = routers[router]
    driver = get_network_driver("ios")
    device = driver(details["ip"], details["username"], details["password"], optional_args={"use_scp" : False})
    device.open()


    #setting router_id
    ospf_config = f"""
    router ospf 1
      router-id {ospf_data[router]["router_id"]}
    """
    #adding network into ospf
    for net, area in ospf_data[router]["networks"]:
        ospf_config += f"  network {net} 0.0.0.255 area {area}\n"


    # adding equal cost for Router 2 and 4
    if router in ["R2", "R4"]:
        ospf_config += """
        maximum-paths 2
        """
    #execute configs
    device.load_merge_candidate(config=ospf_config)
    device.commit_config()
    device.close()

    
    
    return f"OSPF configured on {router}"

# executre OSPF configuration on routers
def configure_all_routers():
    results = []
    for router in ospf_data.keys():
        results.append(to_configure_ospf(router))
    return "\n".join(results)




#main func
if __name__ == "__main__":
    print(configure_all_routers())
