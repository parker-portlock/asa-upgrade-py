# Automated ASA Software Upgrade for HA Pairs (active/passive)
This script is designed to set the boot variable to a user-specified code version, configure th boot variable, then proceed with an in-service software upgrade on the Cisco ASA Platform.

## Requirements
* Python3
* ASA 9.x or newer
* netmiko

## Installation
* install Python 3 onto your system
* install the netmiko package with: `pip3 install netmiko --user`

## Usage
Run the program like so:

`python3 asa-upgrade.py`

You'll be prompted for the file name of the new software, the location of that binary file on the firewall (i.e. flash:), and your user credentials.

There are built-in checks to prevent the upgrade from running if the configuration is not synced, or if the standby firewall in the HA pair is not ready.

### Notes
* This process was *not* tested on ASA 8.x
* The script currently only upgrades one firewall at a time. Multiple HA pair capability is something I would like to implement in the future.
