from pprint import pprint

import db
# import app



class ModelRepository:
    def __init__(self):
        self.command = None
        self.param = None
        model = self.get_model()
        self.klass = self.get_globals()[model]
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

        return self.getOneResult()

    def find_by_term(self, term):
        self.param = {'term': f'%{term}%'}
        self.command = f"SELECT id, title FROM {self.table} WHERE title LIKE :term;"

        return self.getResults()

    def find_one_by_title(self, title):
        self.param = {'title': title.lower()}
        self.command = f"SELECT id, title FROM {self.table} WHERE LOWER(title) = :title;"

        return self.getOneResult()

    def update_title(self, item):
        self.param = {
            'id': item.id,
            'title': item.title,
            'changed': 1
        }
        self.command = f"UPDATE  {self.table} SET title=:title, changed=:changed WHERE id=:id"
        self.execute('update')

    def edit(self, item):
        param = {
            'title': item.title,
            'id_web': item.id_web,
            'changed': item.changed
        }
        if item.id:
            param["id"] = item.id
            command = f"UPDATE {item.table} SET title=:title, id_web=:id_web, changed=:changed WHERE id=:id"
            result = 'one'
        else:
            command = f"INSERT INTO {item.table} (title, id_web, changed) VALUES (:title, :id_web, :changed)"
            result = 'insert'

        response = db.execute_queries([db.Query(command, param, result)])

        if not item.id:
            item.id = response

        return item

    def delete(self, item):
        self.param = {
            'id': item.id
        }
        self.command = f"DELETE FROM {self.table}  WHERE id=:id"
        self.execute('update')

    def find_to_update(self):
        self.command = f"SELECT id, title FROM {self.table} WHERE changed=1;"

        return self.getResults()


class Model:
    def __init__(self, data):
        self.id = None
        self.id_web = None
        self.title = None
        self.changed = 0
        self.parse(data)
        self.table = self.get_table()

    def __str__(self):
        return f"{self.id}, {self.id_web}, {self.title}, {self.changed}"

    @staticmethod
    def get_table():
        pass

    def parse(self, data):
        if data:
            data = dict(data)
            self.id = data.get('id')
            self.id_web = data.get('id_web')
            self.title = data.get('title')
            self.changed = data.get('changed')

    def edit(self):
        return ModelRepository().edit(self)
    #
    # def find(self):
    #     param = {'id': self.id}
    #     command = f"SELECT * FROM {self.table} WHERE id=:id"
    #     data = db.execute_queries([db.Query(command, param, 'one')])
    #     self.parse(data)
    #     return self

    def add_if_not_exist(self):
        if self.id.startswith('#', 0, 1):
            self.title = self.id[1:]
            self.id = None
            self.edit()

        return self
