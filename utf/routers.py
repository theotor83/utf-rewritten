class DatabaseAppsRouter:
    """
    A router to control all database operations on models in the
    auth and contenttypes applications.
    """
    def db_for_read(self, model, **hints):
        """
        Attempts to read auth and contenttypes models go to auth_db.
        """
        if model._meta.app_label == 'archive':
            return 'archive'
        return 'default'

    def db_for_write(self, model, **hints):
        """
        Attempts to write auth and contenttypes models go to auth_db.
        """
        if model._meta.app_label == 'archive':
            return 'archive'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the auth or contenttypes apps is
        involved.
        """
        if obj1._meta.app_label == 'archive' or \
           obj2._meta.app_label == 'archive':
           return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the auth and contenttypes apps only appear in the
        'auth_db' database.
        """
        if app_label == 'archive':
            return db == 'archive'
        return db == 'default' 