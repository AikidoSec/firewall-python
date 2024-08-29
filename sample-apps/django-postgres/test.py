import copy
import psycopg2

psycopg2.connect(
    host="db",
    database="db",
    user="user",
    password="password")

class MutableAikidoConnection:
    """Aikido's mutable connection class"""

    def __init__(self, former_conn):
        self._former_conn = former_conn
        self._cursor_func_copy = copy.deepcopy(former_conn.cursor)

    def __getattr__(self, name):
        #if name != "cursor":
        return getattr(self._former_conn, name)

class Connection:
    def cursor(self):
        return "Hello"

new_mut_aik_class = MutableAikidoConnection(Connection())

new_mut_aik_class.__class__ = Connection.__class__

print(new_mut_aik_class.__class__)
print(isinstance(new_mut_aik_class, Connection))
