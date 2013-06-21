import re
import zipfile
import cgi
from lxml import etree
from lxml import doctestcompare as comp
import cherrypy


_DIFF_RE = re.compile(r'(\(got: [^)]*\))')
def _highlight_diff(s):
  return _DIFF_RE.sub(r'<span class="diff">\1</span>', s)

def _diff_string(gold, test, checker):
  return _highlight_diff(cgi.escape(checker.collect_diff(gold, test, False, 2)))


def test_xpath(doc, gold, test, checker):
  try:
    test_res = doc.xpath(test)
  except:
    return (False, 'Error executing query.')
  gold_res = doc.xpath(gold)
  if type(test_res) != type(gold_res):
    return (False, 'Result types do not match.')
  if type(gold_res) != list:
    gold_res = [gold_res]
    test_res = [test_res]
  if len(gold_res) != len(test_res):
    return (False, \
            'Size of result sets doesn''t match (expected %d, got %d)' % \
              (len(gold_res), len(test_res)))
  n = 0
  for (g, t) in zip(gold_res, test_res):
    n += 1
    if type(g) != type(t):
      return (False, "Types of element %d in result set do not match." % n)
    if ((type(g) == etree._Element) and not checker.compare_docs(g, t)) or \
       ((type(g) == float) and (abs(g-t) > 1e-3*abs(g))) or \
       (g != t):
      return(False, 'Result sets are the same size, ' + \
                    'but elements at position %d differ' % n)  # XXX
  return (True, 'Test passed!')

def test_xslt(doc, gold, test, checker):
  try:
    test_sheet = etree.fromstring(test)
  except:
    return (False, 'Failed to parse XSLT sheet (malformed XML).')
  try:
    test_out = doc.xslt(test_sheet)
  except:
    return (False, 'XSLT parsed succesfully, but transform failed.')
  gold_sheet = etree.fromstring(gold)
  gold_out = doc.xslt(gold_sheet)
  if not checker.compare_docs(gold_out.getroot(), test_out.getroot()):
    diffstr = _diff_string(gold_out.getroot(), test_out.getroot(), checker)
    return(False, 'Output documents differ:<br/><pre>%s</pre>' % diffstr)
  return (True, 'Test passed!')

def test_all(doc, gold_zip, test_zip):
  results = []
  score = 0
  bonus = 0

  conf = cherrypy.request.app.config['test']
  num_questions = conf['num_questions']
  bonus_start = conf['bonus_start']
  filesize_limit = conf['filesize_limit']

  checker = comp.LXMLOutputChecker()

  gold_filenames = gold_zip.namelist()
  for q in range(1, num_questions+1):
    # Figure out what kind of query/transform it is
    if ('q%d.xp' % q) in gold_filenames:
      filename = 'q%s.xp' % q
      test_func = test_xpath
    elif ('q%d.xslt' % q) in gold_filenames:
      filename = 'q%d.xslt' % q
      test_func = test_xslt
    # Check that file is present and satisfies sanity checks
    try:
      info = test_zip.getinfo(filename)
    except KeyError:
      results.append((False, 'File missing from ZIP.'))
      continue
    if info.file_size > filesize_limit:
      results.append((False, \
                     'File size exceeds limit (%d bytes)' % filesize_limit))
      continue
      # Run actual test
    gold = gold_zip.read(filename)
    test = test_zip.read(filename)
    try:
      res = test_func(doc, gold, test, checker)
      results.append(res)
    except:
      results.append((False, 'Unexpected error; please notify instructor:</br>'))
    # Update score or bonus score
    if res[0]:
      if q < bonus_start:
        score += 1
      else:
        bonus += 1
  # Log score to database
  scores_tbl = cherrypy.thread_data.scores
  scores_tbl.insert() \
            .values(username=cherrypy.request.username, 
                    score=score, bonus=bonus) \
            .execute()
  return results

