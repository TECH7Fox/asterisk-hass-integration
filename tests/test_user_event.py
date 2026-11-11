from asterisk.ami import Event

from custom_components.asterisk import ami_user_event_data


def test_ami_user_event_data_normalizes_keys():
    """Test AMI UserEvent payloads are converted to HA event data."""
    event = Event(
        "UserEvent",
        {
            "UserEvent": "CustomAutomation",
            "Source": "pbx",
            "Button": "4",
            "ChannelStateDesc": "Up",
            "Cause-txt": "Normal Clearing",
        },
    )

    assert ami_user_event_data(event) == {
        "event": "UserEvent",
        "user_event": "CustomAutomation",
        "source": "pbx",
        "button": "4",
        "channel_state_desc": "Up",
        "cause_txt": "Normal Clearing",
    }
