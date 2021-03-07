from pprint import pprint

import db
import app


class ModelRepository:
    def __init__(self):
        self.command = None
        self.param = None
        model = self.get_model()
        self.klass = app.get_globals()[model]
        self.table = model.lower()

    @staticmethod
    def get_model():
        pass

    def getResults(self):
        results = db.execute_queries([db.Query(self.command, self.param)])
        return [self.klass(data) for data in results]


    def getOneResult(self):
        result = db.execute_queries([db.Query(self.command, self.param, 'one')])
        return self.klass(result)

    def execute(self, action):
        return db.execute_queries([db.Query(self.command, self.param, action)])

    def find_all(self):
        self.command = f'SELECT * FROM {self.table} ORDER BY title ASC;'

        return self.getResults()

    def find(self, id):
        self.param = {'id': id}
        self.command = f"SELECT * FROM {self.table} WHERE id=:id"
        pprint(self.command)
        pprint(self.param)

        return self.getOneResult()

    def find_by_term(self, term):
        self.param = {'term': f'%{term}%'}
        self.command = f"SELECT id, title FROM {self.table} WHERE title LIKE :term;"

        return self.getResults()

    def update_title(self, item):
        self.param = {
            'id': item.id,
            'title': item.title
        }
        self.command = f"UPDATE  {self.table} SET title=:title WHERE id=:id"
        self.execute('update')

    def delete(self, item):
        self.param = {
            'id': item.id
        }
        self.command = f"DELETE FROM {self.table}  WHERE id=:id"
        self.execute('update')


class Model:
    def __init__(self, data):
        self.id = None
        self.title = None
        self.parse(data)
        self.table = self.get_table()

    def __str__(self):
        return f"{self.id}, {self.title}"

    @staticmethod
    def get_table():
        pass

    def parse(self, data):
        if data:
            data = dict(data)
            self.id = data.get('id')
            self.title = data.get('title')

    def edit(self):
        param = {
            'title': self.title,
        }
        if self.id:
            param["id"] = self.id
            command = f"UPDATE {self.table} SET title=:title WHERE id=:id"
            result = 'one'
        else:
            command = f"INSERT INTO {self.table} (title) VALUES (:title)"
            result = 'insert'

        response = db.execute_queries([db.Query(command, param, result)])

        if not self.id:
            self.id = response

        return self
    #
    # def find(self):
    #     param = {'id': self.id}
    #     command = f"SELECT * FROM {self.table} WHERE id=:id"
    #     data = db.execute_queries([db.Query(command, param, 'one')])
    #     self.parse(data)
    #     return self

    def add_if_not_exist(self):
        pprint(self.id)
        pprint(self.title)
        if self.id.startswith('#', 0, 1):
            self.title = self.id[1:]
            self.id = None
            self.edit()

        return self

