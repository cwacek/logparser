import pkgutil
import functools
import logging
logger = logging.getLogger(__name__)

__all__ = ['Parser', 'available_parsers']


class Parser(object):
  """ Base class for parsers. All parsers
  should define three member attributes:

    :_name: The name of the parser
    :_headers: The header fields for the data
    :_data: The data itself, as a dictionary keyed by
            :headers:

  """

  def __init__(self):
    """Initialize a data object from this parser"""
    raise RuntimeError("Not implemented")

  @property
  def data(self):
    """ Return the data parsed """
    return self._data

  @property
  def desc(self):
    """ Return the parser description """
    return self._desc

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
  def wrapper(*args, **kwargs):
    if not hasattr(fn, 'result'):
      fn.result = fn(*args, **kwargs)

    return fn.result

  return wrapper


def __example_loader__(opts):

  def example_parser_method(line):
    pass
  tmp = [('ex1', example_parser_method),
         ('ex2', example_parser_method)]

  for parser in tmp:
    yield parser


@memoize
def available_parsers(opts):
  """ Import all available parsers

  Parsers are searched for in the logparser.parsers
  namespace. A `parser' is considered to be any
  callable which given a string returns a dictionary of
  data parsed from it or raises a ValueError if the line
  doesn't contain relevant data.

  Since parsers are just callables, it's perfectly reasonable
  to have them be methods on an instance. The same instance
  will then be used on each line, allowing complicated parsers
  which save state to be used

  Parsers are loaded in one of two ways:

  1. __loader__ method

    If a package has a method called __loader__, it will
    be called as a generator and passed a set of global
    options. Each iteration should return tuples containing
    names and parser callables.

    >>> [(x[0], callable(x[1])) for x in __example_loader__({})]
    [('ex1', True), ('ex2', True)]

  2. __virtual__

    A module can define a single parser by providing a
    __virtual__ definition for the parser. This should be
    a tuple containing the name of the parser and a
    callable as described above.
  """

  parsers = {}
  for loader, name, ispkg in pkgutil.iter_modules(__path__):

    actual_loader = loader.find_module(name)
    parser = actual_loader.load_module(actual_loader.fullname)

    if hasattr(parser, '__loader__'):
      for name, cls in parser.__loader__(opts):
        parsers[name] = cls
        logger.debug("Loaded {0} for '{1}'".format(cls, name))

    else:
      try:
        parsers[parser.__virtual__[0]] = parser.__virtual__[1]
        logger.debug("Loaded {0[1]} for '{0[0]}'".format(parser.__virtual__))
      except:
        logger.debug("Failed to load parser from %s" % actual_loader.filename)

  return parsers
