class MockAMIClient:

    event_handlers = {}

    def add_event_listener(self, func, white_list, **kwargs):
        for event in white_list:
            if self.event_handlers.get(event) is None:
                self.event_handlers[event] = []
            self.event_handlers[event].append(func)

    def trigger_event(self, event):
        handlers = self.event_handlers[event["Event"]]
        for handler in handlers:
            handler(event)

    def send_action(self, action):
        pass
