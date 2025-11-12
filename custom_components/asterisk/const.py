DOMAIN = "asterisk"
CLIENT = "client"
AUTO_RECONNECT = "auto_reconnect"
PLATFORMS = [
    "binary_sensor",
    "sensor",
]
STATES = {
    "NOT_INUSE": "Not in use",
    "INUSE": "In use",
    "BUSY": "Busy",
    "UNAVAILABLE": "Unavailable",
    "RINGING": "Ringing",
    "RINGINUSE": "Ringing in use",
    "ONHOLD": "On hold",
    "UNKNOWN": "Unknown",
}
STATE_ICONS = {
    "Not in use": "mdi:phone-hangup",
    "In use": "mdi:phone-in-talk",
    "Busy": "mdi:phone-in-talk",
    "Unavailable": "mdi:phone-off",
    "Ringing": "mdi:phone-ring",
    "Ringing in use": "mdi:phone-ring",
    "On hold": "mdi:phone-paused",
    "Unknown": "mdi:phone-off",
}
SIP_LOADED = "sip_loaded"
PJSIP_LOADED = "pjsip_loaded"
SCCP_LOADED = "sccp_loaded"
IAX_LOADED = "iax_loaded"
