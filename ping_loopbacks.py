#!/usr/bin/env python3
from napalm import get_network_driver

# R1 info
r1_ip = "222.0.0.1"  # Замени на реальный IP R1
username = "admin"    # Замени на свой логин
password = "admin"    # Замени на свой пароль

# Loopbacks of R2, R3, R4
loopbacks = {
    "R2": "20.0.0.1",
    "R3": "30.0.0.1",
    "R4": "40.0.0.1"
}

def ping_from_r1():
    driver = get_network_driver("ios")
    device = driver(r1_ip, username, password, optional_args={"use_scp": False})

    results = {}

    try:
        device.open()
        for router, ip in loopbacks.items():
            output = device.ping(ip)
            print(f"Ping Output for {ip}: {output}")  # Отладка

            # Исправляем: извлекаем "success" правильно
            success = output.get("success", {}).get("packet_loss", 100)
            
            results[router] = {
                "ip": ip,
                "status": "Success" if success < 100 else "Failed"
            }

        device.close()

    except Exception as e:
        results["Error"] = {"ip": "N/A", "status": str(e)}

    return results  # Возвращаем `results`
