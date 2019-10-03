#asa.py

import netmiko

from netmiko import ConnectHandler

def failover (host,username,password): 
    try:
        net_connect = ConnectHandler(device_type='cisco_asa',ip=host,username=username,password=password)
        failAct = "failover exec standby failover active"
        net_connect.send_command(failAct) 
    except:
        pass