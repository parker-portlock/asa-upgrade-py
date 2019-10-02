import sys
import os
import netmiko
import getpass
import time
import re

newVersion = input("Please enter the filename for the asa binary: ")

if newVersion != "":
    
    #show boot configuration in running config
    showBoot = "show run boot\n show version"

    host = input("Hostname/IP: ")
    username = input("Username: ")
    password = getpass.getpass("Password: ")
    from netmiko import ConnectHandler
    net_connect = ConnectHandler(device_type='cisco_asa',ip=host,username=username,password=password)
    currentVersion = net_connect.send_command(showBoot)
    print(currentVersion)




    #start configuration
    #print("config t")
    #print("no", currentVersion)
    #print("boot system", newVersion)
    #print("boot system", currentVersion)
    #print("end")
    #print("wr mem")

    # wait for file to save
    print("Waiting for configuration to save...")
    time.sleep(10)

    # check failover status
    print("Checking failover state...")
    showFailover = "sh failover state"
    net_connect = ConnectHandler(device_type='cisco_asa',ip=host,username=username,password=password)
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
        print("failover reload-standby")

        # wait for the standby to reboot before verifying
        print("Waiting for standby to reload...")
        attempts = 0
        while attempts < 3:
            try:
                showFailover = "sh failover state"
                net_connect = ConnectHandler(device_type='cisco_asa',ip=host,username=username,password=password)
                failoverState = net_connect.send_command(showFailover)
                syncStatus = False
                stdbyStatus = False

                stdbyRed = ['Standby Ready']
                for pattern in stdbyRed:

                    if re.search(pattern,failoverState):
                        print('Standby Booted!')
                        stdbyStatus = True

                syncRed = ['Sync Done']
                for pattern in syncRed:
                    if re.search(pattern,failoverState):
                        print('Config Synced!')
                        syncStatus = True

                if syncStatus == True and stdbyStatus == True:
                    postHA = True
                    attempts = 3
                else:
                    print('Still waiting for standby to boot...')
                    time.sleep(120)
            except:
                attempts += 1
                print('Standby not booted yet...')

        # Start First manual failover
        print("Initiating manual failover...")
        print("failover exec standby failover active")
        time.sleep(30)

        # log into the firewall again
        print("failover reload-standby")
        print("Waiting for new standby to reload...")
        
        # wait for the standby to reboot before verifying
        attempts = 0
        while attempts < 3:
            try:
                showFailover = "sh failover state"
                net_connect = ConnectHandler(device_type='cisco_asa',ip=host,username=username,password=password)
                failoverState = net_connect.send_command(showFailover)
                syncStatus = False
                stdbyStatus = False

                stdbyRed = ['Standby Ready']
                for pattern in stdbyRed:
                    if re.search(pattern,failoverState):
                        print('Standby Booted!')
                        stdbyStatus = True


                syncRed = ['Sync Done']
                for pattern in syncRed:
                    if re.search(pattern,failoverState):
                        print('Config Synced!')
                        syncStatus = True


                if syncStatus == True and stdbyStatus == True:
                    postHA = True
                    attempts = 3
                else:
                    print('Still waiting for standby to boot...')
                    time.sleep(120)
            except:
                attempts += 1
                print('Standby not booted yet...')

        # Start second Manual failover
        print("Initiating manual failover")
        print("failover exec standby failover active")
        time.sleep(30)
        
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