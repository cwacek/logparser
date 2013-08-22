import pkgutil
import logging
logger = logging.getLogger(__name__)


class Parser(object):
  """Docstring for Parser """

  def __init__(self):
    """@todo: to be defined """
    raise RuntimeError("Not implemented")

  @property
  def data(self):
    """ Return the data parsed """
    raise RuntimeError("Not implemented")

  @property
  def name(self):
    return self.name


def available_parsers():
  parsers = {}
  for loader, name, ispkg in pkgutil.iter_modules(__path__):

    actual_loader = loader.find_module(name)
    parser = actual_loader.load_module(actual_loader.fullname)
    try:
      parsers[parser.__virtual__[0]] = parser.__virtual__[1]
      logger.debug("Loaded {0[1]} for '{0[0]}'".format(parser.__virtual__))
    except:
      logger.debug("Failed to load parser from %s" % actual_loader.filename)

  return parsers
