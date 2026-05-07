class MockAMIMessage:
    def __init__(self, name=None, keys=None, error=False):
        self.name = name
        self.keys = keys or {}
        self._error = error

    def __getitem__(self, item):
        return self.keys[item]

    def is_error(self):
        return self._error


class MockActionFuture:
    def __init__(self, response):
        self.response = response


class MockAutoReconnect:
    def __init__(self, client, delay=3):
        self.client = client
        self.delay = delay
        self.name = "MockAutoReconnect"
        self.daemon = False
        self.on_disconnect = None
        self.on_reconnect = None

    def is_alive(self):
        return True


class MockAMIClient:
    def __init__(self, confbridge_rooms=None, confbridge_error_message=None):
        self.confbridge_rooms = confbridge_rooms or []
        self.confbridge_error_message = confbridge_error_message
        self.event_handlers = []
        self.sent_actions = []

    def login(self, username, secret):
        return MockActionFuture(
            MockAMIMessage(
                keys={
                    "Response": "Success",
                    "Message": "Authentication accepted",
                }
            )
        )

    def logoff(self):
        return None

    def disconnect(self):
        return None

    def add_event_listener(self, func, white_list=None, **kwargs):
        listener = {
            "func": func,
            "white_list": list(white_list or []),
            "filters": kwargs,
        }
        self.event_handlers.append(listener)
        return listener

    def remove_event_listener(self, listener):
        if listener in self.event_handlers:
            self.event_handlers.remove(listener)

    def trigger_event(self, event):
        if isinstance(event, dict):
            event = MockAMIMessage(name=event.get("Event"), keys=event)

        for listener in list(self.event_handlers):
            if not self._matches_listener(listener, event):
                continue
            listener["func"](event)

    def send_action(self, action):
        action_name = getattr(action, "name", None)
        action_keys = dict(getattr(action, "keys", {}) or {})
        if action_name is None:
            action_name = action_keys.get("Action")

        self.sent_actions.append({"action": action_name, "keys": action_keys})

        if action_name == "ConfbridgeListRooms":
            action_id = action_keys.get("ActionID")
            if self.confbridge_error_message is not None:
                return MockActionFuture(
                    MockAMIMessage(
                        keys={
                            "Response": "Error",
                            "Message": self.confbridge_error_message,
                            "ActionID": action_id,
                        },
                        error=True,
                    )
                )

            for room in self.confbridge_rooms:
                self.trigger_event(
                    {
                        "Event": "ConfbridgeListRooms",
                        "ActionID": action_id,
                        **room,
                    }
                )

            self.trigger_event(
                {
                    "Event": "ConfbridgeListRoomsComplete",
                    "ActionID": action_id,
                    "EventList": "Complete",
                    "ListItems": str(len(self.confbridge_rooms)),
                }
            )
            return MockActionFuture(
                MockAMIMessage(
                    keys={
                        "Response": "Success",
                        "Message": "Conference rooms will follow",
                        "ActionID": action_id,
                    }
                )
            )

        if action_name == "Ping":
            return MockActionFuture(
                MockAMIMessage(keys={"Response": "Success", "Message": "Pong"})
            )

        if action_name == "CoreSettings":
            return MockActionFuture(
                MockAMIMessage(
                    keys={
                        "Response": "Success",
                        "AsteriskVersion": "20.0.0",
                    }
                )
            )

        if action_name in {"SIPpeers", "PJSIPShowEndpoints"}:
            return MockActionFuture(
                MockAMIMessage(
                    keys={"Response": "Error", "Message": f"{action_name} unavailable"},
                    error=True,
                )
            )

        return MockActionFuture(
            MockAMIMessage(keys={"Response": "Success", "Message": "Action completed"})
        )

    def _matches_listener(self, listener, event):
        white_list = listener["white_list"]
        if white_list and event.name not in white_list:
            return False

        for key, expected_value in listener["filters"].items():
            if event.keys.get(key) != expected_value:
                return False

        return True
