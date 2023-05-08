# Asterisk-integration
**Asterisk integration for Home Assistant**

This integration finds and adds all SIP and PJSIP devices to your Home Assistant.

## Roadmap
Things that are coming soon:
* Device triggers and conditions

I am open for suggestions!

## Asterisk add-on

The [Asterisk add-on](https://github.com/TECH7Fox/asterisk-hass-addons) fully supports this integration.

## Requirements
For this to work you will need the following:
* A sip/pbx server. (I recommend the Asterisk add-on to get started)
* HACS on your Home Assistant.
* Create an AMI manager. Make sure your IP is allowed. (Add-on comes preconfigured for this)

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

* For DTMF signalling to work, in FreePBX, change the dmtf signaling. For intercom purposes, "SIP-INFO DTMF-Relay" is needed.

If you are still having problems you can make an issue, ask on the [discord server](https://discordapp.com/invite/qxnDtHbwuD) or send me a email.

## Contact
**jordy.kuhne@gmail.com**
