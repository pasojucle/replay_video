from model import Model, ModelRepository

class Program(Model):
    @staticmethod
    def get_table():
        return 'program'


class ProgramRepository(ModelRepository):
    @staticmethod
    def get_model():
        return 'Program'

    @staticmethod
    def get_globals():
        return globals()
