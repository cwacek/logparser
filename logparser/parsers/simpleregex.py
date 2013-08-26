import logging
logger = logging.getLogger(__name__)

from logparser.parsers import Parser

import re
import itertools
from pkg_resources import resource_listdir, resource_stream
import yaml

OBJ = lambda **kwargs: type('obj', (object,), kwargs)()


def __loader__(opts):
  """ Load all of the simple YAML regex parsers.

  If 'parsers.simpleregex.files' is provided in :opts:, try and
  load from that path in addition to the built in directory.
  """
  files = resource_listdir('logparser.parsers', 'simple')

  for f in ('simple/{0}'.format(x) for x in files if x[0] != '.'):
    with resource_stream('logparser.parsers', f) as fin:
      try:
        data = yaml.load(fin)
      except Exception as e:
        logging.info("Skipping '{0}'. Invalid format".format(f))
        logging.debug("Load Error: {0}".format(e))
        continue

      for i, parser_data in enumerate(data, 1):
        try:
          parser = SimpleRegex(parser_data)
        except Exception, e:
          logger.debug("Failed to load #{0} parser from {1}: {2}"
                       .format(i, f, e))
        else:
          yield (parser.name, parser.run)

  if 'simpleregex.files' in opts.parser_opts:
    for f in opts.parser_opts['simpleregex.files']:
      with open(f) as fin:
        try:
          data = yaml.load(fin)
        except Exception as e:
          logging.info("Skipping '{0}'. Invalid format".format(f))
          logging.debug("Load Error: {0}".format(e))
          continue

        for i, parser_data in enumerate(data, 1):
          try:
            parser = SimpleRegex(parser_data)
          except Exception, e:
            logger.debug("Failed to load #{0} parser from {1}: {2}"
                         .format(i, f, e))
          else:
            yield (parser.name, parser.run)


def parse_time(timestring, **opts):
  """ Parse a string containing a timestamp into a float.
  If the year is 1900 (i.e it's missing) it will set the
  year to the current year.

  :timestring: The string
  :format: String format as used by datetime.strptime
  :returns: float

  >>> parse_time('Aug 21 18:05:04.000')
  1377108304
  >>> parse_time('2/24/2012 4:25:22 PM', '%m/%d/%Y %I:%M:%S %p')
  1330100722
  """
  import calendar
  from datetime import datetime as dt

  if 'fmt' not in opts:
    opts.update(fmt="%b %d %H:%M:%S.%f")

  date = dt.strptime(timestring, opts['fmt'])
  if date.year == 1900:
    date = date.replace(year=dt.today().year)

  return calendar.timegm(date.utctimetuple())


def parse_list(string, strip=True, **opts):
  """ Parse a list from a string.

  Parse the list by splitting it apart based
  on :separator:. If not defined, defaults to the
  standard behavior of string.split(). Unless :strip:
  is false, strip each split field.

  Return a list containing each value, optionally
  type-converted according to :subtype:. :subtype:
  can be one of SimpleRegex.TYPES.

  >>> parse_list('9 4 3 2 5')
  ['9', '4', '3', '2', '5']

  >>> parse_list('9 4 3 2 5', subtype='int')
  [9, 4, 3, 2, 5]

  >>> parse_list('9 4 3 2.4 5', subtype='float')
  [9.0, 4.0, 3.0, 2.4, 5.0]

  >>> parse_list('James Bond, Sherlock Holmes', split=',')
  ['James Bond', 'Sherlock Holmes']

  >>> parse_list('James Bond, Sherlock Holmes', split=',', strip=False)
  ['James Bond', ' Sherlock Holmes']
  """

  sep = opts['separator'] if 'separator' in opts else None
  fields = string.strip().split(sep)

  if opts['strip']:
    fields = [field.strip() for field in fields]

  if 'subtype' not in opts:
    return fields

  if opts['subtype'] not in SimpleRegex.TYPES.keys():
    raise TypeError("Requested type conversion '{0}' not recognized"
                    .format(opts['subtype']))

  return map(SimpleRegex.TYPES[opts['subtype']], fields)


class SimpleRegex(Parser):
  """ Load YAML defined Regex parsers.
  """
  TYPES = {
      'int': lambda x, **opts: int(x),
      'float': lambda x, **opts: float(x),
      'str': lambda x, **opts: str(x),
      'time': parse_time,
      'list': parse_list,
      'boolean': lambda x, **opts: True if x == opts['truth'] else False
  }

  def __init__(self, yaml):

    self._name = yaml['name']
    self._data = {}

    try:
      self.regex = re.compile(yaml['regex'])
    except AttributeError:
      raise ValueError("No regular expression provided")
    except re.error:
      raise ValueError("Invalid regular expression")

    try:
      self.fields = yaml['fields']
    except:
      raise ValueError("No fields provided. Will work, but is useless")

    if len(self.fields) != self.regex.groups:
      raise ValueError("Number of fields not equivalent to number of "
                       "patterns in regular expression ({0} vs {1})"
                       .format(len(self.fields), self.regex.groups))

    for field in self.fields:
      if field['type'] not in self.TYPES:
        raise ValueError("Field type '{0}' not recognized."
                         .format(field['type']))

  @property
  def headers(self):
    return [field['name'] for field in self.fields]

  def run(self, line):
    """ Actually run the parser. Return an object
      which has the data accessible via the property
      :data: so that we behave pretty much like
      calling __init__ as a regular parser would.
    """

    match = self.regex.match(line)
    if not match:
      raise ValueError

    data = dict(itertools.izip_longest(self.headers, [], fillvalue=None))

    for i, field in enumerate(self.fields, 1):
      matched = match.group(i)

      try:
        data[field['name']] = self.TYPES[field['type']](matched, **field)
      except:
        raise TypeError("Failed to convert '{0}' to type '{1}'"
                        .format(matched, field['type']))

    return OBJ(data=data, name=self.name, headers=self.headers)

__virtual__ = ('SimpleRegex', SimpleRegex)
