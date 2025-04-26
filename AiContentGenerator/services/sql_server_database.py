import pyodbc


class SQLServerDatabase:
    def __init__(self, server, database, username, password):
        self.connection_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};DATABASE={database};UID={username};PWD={password}"
        )
        self.connection = None

    def connect(self):
        try:
            self.connection = pyodbc.connect(self.connection_string)
            print("Database connection established.")
        except Exception as e:
            print(f"Failed to connect to database: {e}")
            raise

    def disconnect(self):
        if self.connection:
            self.connection.close()
            print("Database connection closed.")

    def select(self, query):
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return rows
        except Exception as e:
            print(f"Failed to execute SELECT query: {e}")
            raise

    def insert_and_get_id(self, insert_query):
        try:
            cursor = self.connection.cursor()
            cursor.execute(insert_query)
            cursor.execute("SELECT SCOPE_IDENTITY();")  # Retrieve the last inserted ID
            record_id = cursor.fetchone()[0]
            self.connection.commit()
            return record_id
        except Exception as e:
            print(f"Failed to execute INSERT query: {e}")
            self.connection.rollback()
            raise

    def update(self, update_query):
        try:
            cursor = self.connection.cursor()
            cursor.execute(update_query)
            self.connection.commit()
        except Exception as e:
            print(f"Failed to execute UPDATE query: {e}")
            self.connection.rollback()
            raise
