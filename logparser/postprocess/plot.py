import logparser.postprocess.util as util
import json

import logging
logger = logging.getLogger(__name__)


class SavePlotException(Exception):
  def __init__(self, fname):
    self._fname = fname
    Exception.__init__(self)

  @property
  def filename(self):
    return self._fname


try:
  import rpy2.robjects as ro
  import rpy2.robjects.lib.ggplot2 as ggplot2
except ImportError as e:
  logger.error("Failed to load R extensions (rpy2)")
  logger.debug("ImportError: {0}".format(e))
  raise RuntimeError()


def get_ggplot_args(argparse_args):
  """Get ggplot related arguments from argparse_args

  :argparse_args: cmdline parsed args
  :returns: util.Namespace with ggplot args in it
  """
  ggplot_names = ('x', 'y', 'type')
  ggplot_args = dict(((arg, None) for arg in ggplot_names))
  global_vars = util.Namespace({
      'title': 'LogParser Graph'
  })

  for argname in argparse_args.__dict__:
    if argname in ggplot_names:
      ggplot_args[argname] = getattr(argparse_args, argname)

  global_vars.set('facets', argparse_args.__dict__.get('facets', None))

  return (global_vars, {'cmdline': util.Namespace(ggplot_args)})


def plot(args):
  """ Plot data parsed from logfiles previously """

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
  parsers = [data.values()[0].keys()[0]] if args.p is None else args.p
  dataf = util.filter_and_flatten(data, args.f, parsers, label_files=True)

  r_dataf = ro.DataFrame(dataf.asRObjects)
  gp = ggplot2.ggplot(r_dataf)

  global_vars, geometries = get_ggplot_args(args)
  have_plot = False
  while True:
    try:
      global_vars, geometries = print_menu(global_vars, geometries,
                                           dataf, have_plot)
    except SavePlotException as e:
      try:
        ro.r("ggsave(filename='{0}')".format(e.filename))
      except IOError as io:
        logging.warn("Error saving plot: {0}".format(io))
    except StopIteration:
      return
    have_plot = render_plot(gp, geometries, global_vars)


def geometry_prompt(current=None):
  """ Ask the user whe specification the new geometry
  should have.
  """
  if current is None:
    print("Creating new geometry")
    current = util.Namespace({})

  current.set('x',
              util.prompt('x-axis', current.get('x', None))) \
         .set('y',
              util.prompt('y-axis', current.get('y', None))) \
         .set('col.aes',
              util.prompt('data-varied color',
                          current.get('col.aes', None))) \
         .set('col.fixed',
              util.prompt('fixed color',
                          current.get('col.fixed', None)))   \
         .set('type',
              util.prompt('type (line, point, smooth)',
                          current.get('type', None)))

  return current


def print_menu(global_vars, geometries, dataframe, have_plot):
  """Allow people to plot different things
  without exiting

  :global_vars: Global variables and settings
  :geometries: The current set of geometries
  :dataframe: The dataframe we're working with
  :returns: New plot args
  """

  plotcmd = 'replot' if have_plot else 'plot'

  commands = util.Namespace({})

  commands.set('modify <geomlabel>', 'Modify an existing geometry') \
          .set('add <geomlabel>', 'Create new geometry with label') \
          .set('rm <geomlabel>', 'Remove geometry') \
          .set(plotcmd, 'Plot with current settings')               \
          .set('peek <n>', 'Peek at the top <n> rows of data')      \
          .set("set <var> <va>", 'Set global variable ')

  if have_plot:
    commands.set('save <filename>', 'Save the current plot to <filename>')

  commands.set('quit', 'Exit the plotter')

  while True:
    print("Geometries:")
    for label, geometry in geometries.iteritems():
      print("{0}".format(label))
      print("---------")
      print("{geom}".format(geom=geometry.prettyprint()))
      print("")

    print("Globals:")
    print("{globvars}".format(globvars=global_vars.prettyprint()))
    print("")

    print("Commands:")
    print("{cmds}".format(cmds=commands.prettyprint()))

    cmd = raw_input('> ').strip().split()

    if len(cmd) < 1:
      continue

    if cmd[0] == 'quit':
      raise StopIteration()

    if cmd[0] == 'set':
      try:
        global_vars[cmd[1]] = cmd[2].strip()
      except IndexError:
        print("Invalid parameters to 'set'")

    if cmd[0] == 'add':
      try:
        if cmd[1] in geometries:
          raise KeyError
        geometries[cmd[1]] = geometry_prompt()
      except IndexError:
        print("'add' requires a geometry label")
      except KeyError:
        print("Geometry '{0}' already defined".format(cmd[1]))

    if cmd[0] == 'modify':
      try:
        if cmd[1] not in geometries:
          raise KeyError
        geometries[cmd[1]] = geometry_prompt(geometries[cmd[1]])
      except IndexError:
        print("'add' requires a geometry label")
      except KeyError:
        print("Geometry '{0}' not defined".format(cmd[1]))

    if cmd[0] == 'rm':
      try:
        if cmd[1] not in geometries:
          raise KeyError
        del geometries[cmd[1]]
      except IndexError:
        print("'add' requires a geometry label")
      except KeyError:
        print("Geometry '{0}' not defined".format(cmd[1]))

    if cmd[0] == 'peek':
      try:
        print("DATA: ")
        print(" ".join(dataframe.headers))
        for row in dataframe.by_row(int(cmd[1]), convert=str):
          print(" ".join(row))
        print("")
      except IndexError:
        print("Too many rows to peek")
      except ValueError:
        print("Couldn't parse row number")

    if cmd[0] in ('replot', 'plot'):
      return geometries

    if cmd[0] == 'save':
      raise SavePlotException(cmd[1])


def render_plot(gp, args):
  """Render a plot using ggplot

  :gp: A base ggplot2 object
  :x: The x value expression
  :y: The y value expression
  :type: The type of plot to make

  """
  args = util.Namespace(args)

  import rpy2.robjects.lib.ggplot2 as ggplot2

  pp = gp + ggplot2.aes_string(x=args.x,
                               y=args.y)

  if args.type == 'points':
    pp += ggplot2.geom_point()
  elif args.type == 'lines':
    pp += ggplot2.geom_line()
  elif args.type == 'boxplot':
    pp += ggplot2.geom_boxplot()
  else:
    raise Exception("{0} not implemented".format(args.type))

  if args.facets is not None:
    try:
      pp += ggplot2.facet_grid(ro.Formula(args.facets))
    except Exception:
      pass

  try:
    pp.plot()
  except Exception:
    pass
  else:
    return True
