import sys
import os
import netmiko
import getpass
import time
import re

newVersion = input("Please enter the filename for the asa binary: ")
fileLoc = input("Where is this file saved? (ex. flash:) ")
from netmiko import ConnectHandler

def failover (host,username,password): 
    try:
        net_connect = ConnectHandler(device_type='cisco_asa',ip=host,username=username,password=password)
        failAct = "failover exec standby failover active"
        net_connect.send_command(failAct) 
    except:
        pass

def waitBoot():
    print("Waiting for standby to reload...")
    attempts = 0
    while attempts < 10:
        try:
            showFailover = "sh failover state"
            failoverState = net_connect.send_command(showFailover)
            syncStatus = False
            stdbyStatus = False
            stdbyRed = ['Standby Ready']

            for pattern in stdbyRed:
                if re.search(pattern,failoverState):
                    stdbyStatus = True
            syncRed = ['Sync Done']

            for pattern in syncRed:
                if re.search(pattern,failoverState):
                    syncStatus = True

            if syncStatus == True and stdbyStatus == True:
                postHA = True
                attempts = 10

            else:
                print('Still waiting for standby to boot...')
                time.sleep(30)
        except:
            attempts += 1
            print('Standby not booted yet...')

if newVersion != "":
    
    #show boot configuration in running config
    showBoot = "show run boot"

    host = input("Hostname/IP: ")
    username = input("Username: ")
    password = getpass.getpass("Password: ")
    net_connect = ConnectHandler(device_type='cisco_asa',ip=host,username=username,password=password)
    currentVersion = net_connect.send_command(showBoot)

    newLoc = fileLoc + newVersion
    #start configuration
    if currentVersion != '':
        configBoot = "config t\n" + "no " + currentVersion + "\n" + "boot system " + newLoc + "\n" + currentVersion + "\n" + "end\n" + "wr mem\n"
        net_connect.send_command(configBoot)

    else:
        configBoot = "config t\n" + "boot system " + newLoc + "\n" + "end\n" + "wr mem\n"
        net_connect.send_command(configBoot)

    # wait for file to save
    print("Waiting for configuration to save...")
    time.sleep(10)

    # check failover status
    print("Checking failover state...")
    showFailover = "sh failover state"
    failoverState = net_connect.send_command(showFailover)

    # initializes booleans for checking the standby state and configuration sync status
    syncStatus = False
    stdbyStatus = False


    stdbyRed = ['Standby Ready']
    for pattern in stdbyRed:
        if re.search(pattern,failoverState):
            print('Standby Ready!')
            stdbyStatus = True
        else:
            print('no match')

    syncRed = ['Sync Done']
    for pattern in syncRed:

        if re.search(pattern,failoverState):
            print('Config Synced!')
            syncStatus = True
        else:
            print('no match')

    if syncStatus == True and stdbyStatus == True:

        # start upgrade process
        print("Starting upgrade...")
        reloadStdby = 'failover reload-standby'
        net_connect.send_command(reloadStdby)
        # need a pause to give the firewall time to actually initiate the reboot
        time.sleep(30)
        # wait for the standby to reboot before verifying
        waitBoot()

        # Start First manual failover=
        print("Initiating manual failover...")
        failover(host,username,password)
        time.sleep(10)

        print('Logging back in...')
        net_connect = ConnectHandler(device_type='cisco_asa',ip=host,username=username,password=password)
        net_connect.send_command(reloadStdby)

        # wait for secondary to come back
        waitBoot()

        # Start second Manual failover
        print("Initiating manual failover back to primary...")
        failover(host,username,password)
        time.sleep(10)
        #net_connect.disconnect()

        upgradeSuccess = False
        postHA = False
        # Upgrade Verification
        print("Verifying new software version...")
        # check bootvar
        showBootVar = "show bootvar"
        net_connect = ConnectHandler(device_type='cisco_asa',ip=host,username=username,password=password)
        bootVar = net_connect.send_command(showBootVar)

        postBoot = [newVersion]
        for pattern in postBoot:
            if re.search(pattern,bootVar):
                print('Verified new software version.')
                upgradeSuccess = True
                
            else:
                print("Software version does not match intended upgrade version. Please check your configuration.")
                print("Current bootvar = ", bootVar)
                print("Expected bootvar file = ", newVersion)
                sys.exit()

        if upgradeSuccess == True:
            print("Checking Failover status...")

            # reset failover checks
            syncStatus = False
            stdbyStatus = False

            for pattern in stdbyRed:
                if re.search(pattern,failoverState):
                    stdbyStatus = True
                else:
                    print('no match')

            syncRed = ['Sync Done']
            for pattern in syncRed:
                if re.search(pattern,failoverState):
                    syncStatus = True
                else:
                    print('no match')

            if syncStatus == True and stdbyStatus == True:
                print('Upgrade complete.')
                net_connect.disconnect()
                sys.exit()

    elif syncStatus == False and stdbyStatus == True:
        print('Configuration Status is not synced. Please check your failover configuration and try again.')
        sys.exit()

    elif syncStatus == True and stdbyStatus == False:
        print('Standby is not in a "ready" state. Please check your failover configuration and try again.')
        sys.exit()

    else:
        print('The standby state is not "ready" and the configuration is not synced. Please check your failover configuration and try again.')
        sys.exit()