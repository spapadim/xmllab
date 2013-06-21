import cherrypy
from sqlalchemy import create_engine, MetaData, Table

def check_db():
  if not hasattr(cherrypy.thread_data, 'db'):
    conf = cherrypy.request.app.config['db']
    db = create_engine('mysql://%s:%s@localhost/%s' % \
                       (conf['username'], conf['password'], conf['database']))
    cherrypy.thread_data.db = db
    metadata = MetaData(db)
    cherrypy.thread_data.students = Table('student', metadata, autoload=True)
    cherrypy.thread_data.scores = Table(conf['score_table'], metadata, autoload=True)
    cherrypy.thread_data.scoreboard = Table(conf['scoreboard_table'], metadata, autoload=True)

