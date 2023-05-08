# Asterisk-integration
**Asterisk integration for Home Assistant**

This integration finds and adds all extensions to your Home Assistant and includes a card to call them from.

## Roadmap
Things that are coming soon:
* Device triggers, conditions (actions?)

I am open for suggestions!

## Asterisk add-on

The Asterisk add-on fully supports this integration.

## Requirements
For this to work you will need the following:
* A sip/pbx server. (I recommend the Asterisk add-on to get started)
* Extension for every device. (Add-on auto-generates them)
* HACS on your Home Assistant.
* Create an AMI manager. (Add-on comes with preconfigured with it) For FreePBX look at https://github.com/TECH7Fox/Asterisk-integration/wiki/Setup-AMI-in-FreePBX.


Go to https://github.com/TECH7Fox/HA-SIP/wiki/Setup-FreePBX to see how to setup FreePBX for this card.

## Installation
Download using **HACS**
 1. Go to HACS
 2. Click on the 3 points in the upper right corner and click on `Custom repositories`
 3. Paste https://github.com/TECH7Fox/Asterisk-integration/ into `Add custom repository URL` and by category choose Integration
 4. Click on add and check if the repository is there.
 5. You should now see Asterisk integration. Click `INSTALL`
 6. Restart Home Assistant.
 7. Go to integrations and find Asterisk.
 8. Fill in the fields and click add. If succesful, you should now see your PJSIP/SIP devices.


## Troubleshooting
Most problems is because your PBX server is not configured correct.
To see how to configure FreePBX go to: https://github.com/TECH7Fox/HA-SIP/wiki/Setup-FreePBX

* For DTMF signalling to work, in FreePBX, change the dmtf signaling. For intercom purposes, "SIP-INFO DTMF-Relay" is needed.

If you are still having problems you can make an issue, ask on the discord server or send me a email.

## Contact
**jordy.kuhne@gmail.com**
