import json
from itertools import izip_longest
import sys
import fnmatch
import logging
logger = logging.getLogger(__name__)


class Namespace(dict):
  def __init__(self, d):
    self._d = d

  def __getattr__(self, key):
    return self._d[key]


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
    for key in self.raw:
      if isinstance(self.raw[key][0], (int)):
        conv[key] = ro.IntVector(self.raw[key])
      elif isinstance(self.raw[key][0], (float)):
        conv[key] = ro.FloatVector(self.raw[key])
      elif isinstance(self.raw[key][0], (str)):
        conv[key] = ro.StrVector(self.raw[key])

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

  def by_row(self):
    for i in xrange(self.row_count):
      yield [self._data[key][i] for key in self.headers]

  def __len__(self):
    return self.row_count


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
      headernames = [key
                     for key, val in json_data[fname][parser][0].iteritems()
                     if isinstance(val, (float, int, basestring))]
      if label_files:
        headernames.append('_sourcefile')

      datapoints = DataFrame(headernames)

    for dp in json_data[fname][parser]:
      datapoints.add_row(_sourcefile=fname, **dp)

  return datapoints


def flatten(args):
  """ Flatten an output file to create tabular data """

  try:
    with open(args.input) as fin:
      data = json.load(fin)
  except json.error as e:
    logger.error("Invalid input file. Expected JSON")
    logger.debug("JSON Error: {0}".format(e))
    raise RuntimeError()
  except IOError as e:
    logger.error("Could not read '{0}'".format(args.input))
    logger.debug("IOError: {0}".format(e))
    raise RuntimeError()

  # Get the first one
  parser = data.values()[0].keys()[0] if args.p is None else args.p

  flattened = filter_and_flatten(data, args.f, parser)

  print(" ".join(flattened.headers))

  for row in flattened.by_row():
    print(" ".join(row))


def plot(args):
  """ Plot data parsed from logfiles previously """
  try:
    import rpy2.robjects as ro
    import rpy2.robjects.lib.ggplot2 as ggplot2
  except ImportError as e:
    logger.error("Failed to load R extensions (rpy2)")
    logger.debug("ImportError: {0}".format(e))
    raise RuntimeError()

  try:
    with open(args.input) as fin:
      data = json.load(fin)
  except IOError as e:
    logger.error("Could not read '{0}'".format(args.input))
    logger.debug("IOError: {0}".format(e))
    raise RuntimeError()
  except Exception as e:
    logger.error("Invalid input file. Expected JSON")
    logger.debug("JSON Error: {0}".format(e))
    raise RuntimeError()

  # Get the first one
  parser = data.values()[0].keys()[0] if args.p is None else args.p
  dataf = filter_and_flatten(data, args.f, parser)

  r_dataf = ro.DataFrame(dataf.asRObjects)
  gp = ggplot2.ggplot(r_dataf)

  render_plot(gp, x=args.x, y=args.y, type='points')
  choice = raw_input('Press any key to continue')


def render_plot(gp, **args):
  """Render a plot using ggplot

  :gp: A base ggplot2 object
  :x: The x value expression
  :y: The y value expression
  :type: The type of plot to make

  """
  args = Namespace(args)

  import rpy2.robjects.lib.ggplot2 as ggplot2

  pp = gp + ggplot2.aes_string(x=args.x,
                               y=args.y)

  if args.type == 'points':
    pp += ggplot2.geom_point()
  elif args.type == 'lines':
    pp += ggplot2.geom_lines()
  else:
    raise Exception("{0} not implemented".format(args.type))

  print("Plotting: X='{x}', Y='{y}', type='{type}'")

  pp.plot()

