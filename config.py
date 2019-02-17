import os.path
basedir = os.path.abspath(os.path.dirname(__file__))

DEBUG = True
SECRET_KEY = "nome-seguro"

SQLALCHEMY_DATABASE_URI = 'sqlite+pysqlite:///storage.db' 
SQLALCHEMY_TRACK_MODIFICATIONS = True