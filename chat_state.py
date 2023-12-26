class ChatState:
    _instance = None

    DEFAULT_CHAT_STATE = {
        'initiate_chat_task_created': False,
        'in_chat_mode': False,
        'current_mode': None,
        'input_future': None
    }

    @classmethod
    def getInstance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if self._instance is not None:
            raise ValueError("An instantiation already exists!")
        self.__dict__.update(self.DEFAULT_CHAT_STATE)

    def reset(self):
        self.__dict__.update(self.DEFAULT_CHAT_STATE)