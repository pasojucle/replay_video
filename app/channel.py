from model import Model, ModelRepository

class Channel(Model):
    @staticmethod
    def get_table():
        return 'channel'

class ChannelRepository(ModelRepository):
    @staticmethod
    def get_model():
        return 'Channel'

    @staticmethod
    def get_globals():
        return globals()
