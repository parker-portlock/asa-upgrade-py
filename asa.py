#asa.py

import netmiko

def failover (host,username,password):
    from netmiko import ConnectHandler
    try:
        net_connect = ConnectHandler(device_type='cisco_asa',ip=host,username=username,password=password)
        failAct = "failover exec standby failover active"
        net_connect.send_command(failAct) 
    except:
        pass