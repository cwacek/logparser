import pkgutil
import functools
import logging
logger = logging.getLogger(__name__)


class Parser(object):
  """Docstring for Parser """

  def __init__(self):
    """Initialize a data object from this parser"""
    raise RuntimeError("Not implemented")

  @property
  def data(self):
    """ Return the data parsed """
    return self._data

  @property
  def name(self):
    return self._name

  @property
  def headers(self):
    """ Get the headers that this parser provides"""
    return self._headers

  def __repr__(self):
    return str(self.data)


def memoize(fn):
  @functools.wraps(fn)
  def wrapper():
    if not hasattr(fn, 'result'):
      fn.result = fn()

    return fn.result

  return wrapper


@memoize
def available_parsers():
  parsers = {}
  for loader, name, ispkg in pkgutil.iter_modules(__path__):

    actual_loader = loader.find_module(name)
    parser = actual_loader.load_module(actual_loader.fullname)

    if hasattr(parser, '__loader__'):
      for name, cls in parser.__loader__():
        parsers[name] = cls
        logger.debug("Loaded {0} for '{1}'".format(cls, name))

    else:
      try:
        parsers[parser.__virtual__[0]] = parser.__virtual__[1]
        logger.debug("Loaded {0[1]} for '{0[0]}'".format(parser.__virtual__))
      except:
        logger.debug("Failed to load parser from %s" % actual_loader.filename)

  return parsers
