<<<<<<< HEAD
from content_manager.content_database import ContentDatabase
from content_manager.content_manager import ContentManager
=======
from services.llm_service import QService
from services.sql_server_database import SQLServerDatabase


class ContentDatabase:
    def __init__(self, server, database, username, password):
        self.db = SQLServerDatabase(server, database, username, password)

    def connect(self):
        self.db.connect()

    def disconnect(self):
        self.db.disconnect()

    def get_purecontent_without_description(self):
        query = "SELECT Id, Title FROM dbo.TblPureContent  WHERE Description IS NULL OR ContentCategoryId IS NULL"
        return self.db.select(query)
    
    def get_emotional_tone(self):
        query = "SELECT Id, Title FROM dbo.TblContentEmotionalTone"
        return self.db.select(query)

    def get_language(self):
        query = "SELECT Id, Title FROM dbo.TblContentLanguage"
        return self.db.select(query)

    def get_tone_style(self):
        query = "SELECT Id, Title FROM dbo.TblContentToneStyle"
        return self.db.select(query)

    def get_category(self):
        query = "SELECT Id, Title FROM dbo.TblContentCategory"
        return self.db.select(query)

    def update_pure_content(self, content_id, description, content_category_id):
        update_query = f'''
        UPDATE dbo.TblPureContent
        SET Description = '{description}', ContentCategoryId = {content_category_id}, CompleteDatetime = GETDATE()
        WHERE Id = {content_id}
        '''
        self.db.update(update_query)
        return True


class ContentManager:
    def __init__(self, session_hash, db_instance):
        self.q_service = QService(session_hash)
        self.db = db_instance

    def process_categories(self):
        self.db.connect()
        categories = self.db.get_category()
        for category in categories:
            print(category[0])
        self.db.disconnect()

>>>>>>> b52192f006f1aee2560f5538891991d076360ec7

if __name__ == "__main__":
    SERVER = "45.149.76.141"
    DATABASE = "ContentGenerator"
    USERNAME = "admin"
    PASSWORD = "HTTTHFocBbW5CM"
    SESSION_HASH = "amir"
<<<<<<< HEAD
    
    content_db = ContentDatabase(SERVER, DATABASE, USERNAME, PASSWORD)
    content_manager = ContentManager(SESSION_HASH, content_db)

    content_manager.process_incomplete_contents()

=======

    content_db = ContentDatabase(SERVER, DATABASE, USERNAME, PASSWORD)
    content_manager = ContentManager(SESSION_HASH, content_db)
    content_manager.process_categories()
>>>>>>> b52192f006f1aee2560f5538891991d076360ec7
