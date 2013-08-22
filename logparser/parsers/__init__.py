import pkgutil

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
  for loader, name, ispkg in pkgutil.walk_packages('logparser.parsers'):
    import pdb; pdb.set_trace()
    pass

