import fnmatch
import itertools
import logging
logger = logging.getLogger(__name__)


class Namespace(dict):
  def __init__(self, d):
    self.update(d)

  def __getattr__(self, key):
    return self[key]

  def set(self, key, val):
    self[key] = val
    return self

  def prettyprint(self):
    rep = ""
    for key, val in self.iteritems():
      rep += "\t{0:<20} '{1}'\n".format(key, val)
    return rep


class DataFrame(object):

  @property
  def headers(self):
    return self._headers

  @property
  def raw(self):
    return self._data

  @property
  def asRObjects(self):
    import rpy2.robjects as ro
    conv = {}
    for key in self.headers:
      if isinstance(self.raw[key][0], (int)):
        conv[key] = ro.IntVector(self.raw[key])
      elif isinstance(self.raw[key][0], (float)):
        conv[key] = ro.FloatVector(self.raw[key])
      elif isinstance(self.raw[key][0], (basestring)):
        conv[key] = ro.StrVector(self.raw[key])
      else:
        logger.warn("Failed to convert '{0}' to R Vector".format(key))

    return conv

  def __init__(self, headers):
    self._headers = headers

    self._data = dict(((x, list()) for x in headers))
    self.row_count = 0

  def add_row(self, allow_missing=False, **kwargs):
    for key in self.headers:
      try:
        self._data[key].append(kwargs[key])
      except:
        if allow_missing:
          pass
        raise

    self.row_count += 1

  def by_row(self, limit=None, convert=None):
    limit = self.row_count if limit is None else limit
    if convert is None:
      convert = lambda x: x

    for i in xrange(limit):
      yield [convert(self._data[key][i]) for key in self.headers]

  def __len__(self):
    return self.row_count


def _select_datarow(data, fname, parsers):
  """
  Pull a datarow that combines data from each of the parsers
  and tees it together.

  If the parsers have uneven amounts of data, then the extra
  datarows will be populated with None.

  The data is returned as a dictionary The data will be
  returned in sequences, in the order of the headers for the
  parser, with the parser data arrayed in the order it
  is passed in.
  """
  parser_data = [data[fname][parser] for parser in parsers]

  for data in itertools.izip_longest(*parser_data, fillvalue=None):
    yield(join_datadict(parsers, data))


def join_datadict(parsernames, parserdata):
  """
  Join data from an arbitrary number of parsers,
  updating the keys to be specific to each parser.
  """
  ret = {}
  for name, parser in itertools.izip(parsernames, parserdata):
    if parser is None:
      raise StopIteration
    for datakey, datapoint in parser.iteritems():
      ret['{0}.{1}'.format(name, datakey)] = datapoint

  return ret


def filter_and_flatten(json_data, filefilter, parser, label_files=False):
  """ Return a filtered set of the :json_data:.

  Return data from :parser: and from files which
  match :filefilter:.

  If :label_files: is True, add a column to each row
  annotating which file it came from
  """

  datapoints = None

  for fname in fnmatch.filter(json_data.iterkeys(), filefilter):
    logger.info("Processing {0}".format(fname))
    if datapoints is None:
      # Only include headers which are standard datatypes
      if len(parser) == 1:
        headernames = [key
                       for key, val in json_data[fname][parser][0].iteritems()
                       if isinstance(val, (float, int, basestring))]
      else:
      # Add headers for all the parsers
        headernames = []
        for p in parser:
          p_headers = ["{0}.{1}".format(p, key)
                       for key, val in json_data[fname][p][0].iteritems()
                       if isinstance(val, (float, int, basestring))]
          headernames.extend(p_headers)

      if label_files:
        headernames.append('file_')

      datapoints = DataFrame(headernames)

    for dp in _select_datarow(json_data, fname, parser):
      datapoints.add_row(file_=fname, **dp)

  return datapoints


def prompt(label, default=''):
  """ Prompt for a user value with :label:.
  Allow users to just hit enter if :default: is not
  None.
  """
  entry = raw_input('{label}: [{cur}] '
                    .format(label=label, cur=default))

  if len(entry.strip()) == 0:
    return default

  return entry.strip()
