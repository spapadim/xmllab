import sys, os
import zipfile
import datetime
import cherrypy
from lib import template, auth, db, test
from lxml import etree

path_base = os.path.dirname(__file__)
path_config = os.path.join(path_base, 'config.ini')
path_static = os.path.join(path_base, 'static')
path_data = os.path.join(path_base, 'data')

## mod_python startup
#def start_modpython():
#  cherrypy.tree.mount(XmlApp(), '/xml', config=path_config)
#  cherrypy.config.update({
#    'tools.staticdir.root' : path_static
#  })
#  #cherrypy.engine.start(blocking=False)

# WSGI startup
def application(environ, start_response):
  cherrypy.tree.mount(XmlApp(), '/xml', config=path_config)
  cherrypy.config.update({
    'tools.staticdir.root' : path_static
  })
  return cherrypy.tree(environ, start_response)
 

class XmlApp:
  def __init__ (self):
    self.doc = etree.parse(os.path.join(path_data, "imdb.xml"))  # XXX

  @cherrypy.expose
  @auth.require
  @template.output('index.html')
  def index(self):
    return template.render(title='Hello')

  @cherrypy.expose
  @template.output('login.html')
  def login(self, username=None, password=None):
    auth.check_login(username, password)
    return template.render(username=username)

  @cherrypy.expose
  def logout(self):
    auth.logout()

  @cherrypy.expose
  @auth.require
  @template.output('xpath.html')
  def xpath(self, xpath=None):
    exc = None  # traceback
    elts = []
    if xpath:
      try:
        elts = self.doc.xpath(xpath)
        if type(elts) != type([]):
          elts = [elts]
      except:
        exc = sys.exc_info()
    return template.render(xpath=xpath, elts=elts, exc=exc)

  @cherrypy.expose
  @auth.require
  @template.output('xslt.html')
  def xslt(self, xslt_s=None, xslt_f=None):
    exc = None
    xslt = None
    filename = None
    doc = None
    if xslt_f and xslt_f.file:
      xslt = xslt_f.file.read()
      filename = xslt_f.filename
    elif xslt_s:
      xslt = xslt_s
    if xslt:
      try:
        xslt_doc = etree.fromstring(xslt)
        doc = self.doc.xslt(xslt_doc)
      except:
        exc = sys.exc_info()
    return template.render(xslt_s=xslt, filename=filename, doc=doc, exc=exc)

  @cherrypy.expose
  @auth.require
  @template.output('test.html')
  def test(self, zip_f=None):
    results = []
    if zip_f and zip_f.file:
      db.check_db()
      conf = cherrypy.request.app.config['test']
      # Run tests
      try:
        gold_zip = zipfile.ZipFile(conf['gold_zip'], 'r')
        test_zip = zipfile.ZipFile(zip_f.file)
        results = test.test_all(self.doc, gold_zip, test_zip)
      finally:
        gold_zip.close()
        test_zip.close()
      # Log zipfile submission
      timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
      filename = '%s/%s_%s.zip' % (conf['logdir'], timestamp, \
                                   cherrypy.request.username)
      fp = open(filename, 'w')
      try:
        fp.write(zip_f.fullvalue())
      finally:
        fp.close()
    return template.render(results=results)

  @cherrypy.expose
  @auth.require
  @template.output('scores.html')
  def scores(self):
    db.check_db()
    scoreboard = cherrypy.thread_data.scoreboard
    scores = scoreboard.select().execute().fetchall()
    return template.render(scores=scores)

