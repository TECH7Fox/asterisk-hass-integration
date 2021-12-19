# Asterisk-integration
**Asterisk integration for Home Assistant**

This integration finds and adds all extensions to your Home Assistant and includes a card to call them from.

## Roadmap
Things that are coming soon:
* Video
* GUI config
* More useful text
* Better styling
* Device triggers, conditions and actions
* More entities with information
* Support popup

Less priority:
* Channel entities
* PA/broadcast
* conference
* forward calls

I am open for suggestions!

## Asterisk add-on

The upcoming Asterisk add-on will be fully supported by this integration.

## Requirements
For this to work you will need the following:
* A sip/pbx server. (I use freepbx on a raspberry)
* Extension for every device.
* HACS on your Home Assistant.
* Create an AMI manager. For FreePBX look at https://github.com/TECH7Fox/Asterisk-integration/wiki/Setup-AMI-in-FreePBX.


Go to https://github.com/TECH7Fox/HA-SIP/wiki/Setup-FreePBX to see how to setup FreePBX for this card.

## Installation
Download using **HACS**
 1. Go to HACS
 2. Click on the 3 points in the upper right corner and click on `Custom repositories`
 3. Paste https://github.com/TECH7Fox/Asterisk-integration/ into `Add custom repository URL` and by category choose Lovelace
 4. Click on add and check if the repository is there.
 5. You should now see Asterisk integration. Click `INSTALL`
 6. Restart Home Assistant.
 7. Go to integrations and find Asterisk.
 8. Fill in the fields and click add.
 9. Check if the card loads succesfully.

## Usage
Add the card by setting **type** to `custom:sipjs-card`.

````
type: custom:sipjs-card
server: 192.168.0.1
autoAnswer: true
entities:
  - entity: sensor.asterisk_extension_103
    person: person.someone
    secret: 1234
  - entity: sensor.asterisk_extension_104
    person: person.someone_else
    secret: 1234
dtmfs:
  - name: door
    signal: 1
````

## Troubleshooting
Most problems is because your pbx server is not configured correct.
To see how to configure FreePBX go to: https://github.com/TECH7Fox/HA-SIP/wiki/Setup-FreePBX

* For DTMF signalling to work, in FreePBX, change the dmtf signalling. For intercom purposes, "SIP-INFO DTMF-Relay" is needed.
* Android companion app doesn't work, it's not possible to grant permissions to audio + speaker, this is fixed in the BETA android app. In the android Play Store, subscribe to the BETA channel.

If you are still having problems you can make an issue, ask on the discord server or send me a email.

## Contact
**jordy.kuhne@gmail.com**
