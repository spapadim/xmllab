import cherrypy
from lib import db

# XXX Hardcoded URLs suck..

SESSION_KEY = '_xmllab_user'

def require(func):
  def wrapper(*args, **kwargs):
    username = cherrypy.session.get(SESSION_KEY)
    if not username:
      raise cherrypy.HTTPRedirect('https://dbm-rbs.rutgers.edu/xml/login')
    cherrypy.request.username = username
    return func(*args, **kwargs)
  return wrapper


def check_login(username=None, password=None):
  if username is not None:
    db.check_db()
    students = cherrypy.thread_data.students
    row = students.select().where(students.c.username == username).execute().fetchone()
    if (row is not None) and (password == row['password']):
      cherrypy.session[SESSION_KEY] = username
      raise cherrypy.HTTPRedirect("https://dbm-rbs.rutgers.edu/xml")

def logout():
  cherrypy.session[SESSION_KEY] = None
  raise cherrypy.HTTPRedirect("https://dbm-rbs.rutgers.edu/xml/login")
