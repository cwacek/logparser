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
  ggplot_names = ('x', 'y', 'type', 'facets')
  ggplot_args = dict(((arg, None) for arg in ggplot_names))

  for argname in argparse_args.__dict__:
    if argname in ggplot_names:
      ggplot_args[argname] = getattr(argparse_args, argname)

  return util.Namespace(ggplot_args)


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

  plotargs = get_ggplot_args(args)
  have_plot = False
  while True:
    try:
      plotargs = print_menu(plotargs, dataf, have_plot)
    except SavePlotException as e:
      try:
        ro.r("ggsave(filename='{0}')".format(e.filename))
      except IOError as io:
        logging.warn("Error saving plot: {0}".format(io))
    except StopIteration:
      return
    have_plot = render_plot(gp, plotargs)


def print_menu(plot_args, dataframe, have_plot):
  """Allow people to plot different things
  without exiting

  :plot_args: The current plot args
  :dataframe: The dataframe we're working with
  :returns: New plot args
  """

  plotcmd = 'replot' if have_plot else 'plot'

  commands = util.Namespace({})

  commands.set('set <var> <value>', 'Set a variable to a new value') \
          .set(plotcmd, 'Plot with current variables') \
          .set('peek <n>', 'Peek at the top <n> rows of data')

  if have_plot:
    commands.set('save <filename>', 'Save the current plot to <filename>')

  commands.set('quit', 'Exit the plotter')

  while True:
    print("""Current Values:
{plotargs}

Commands:
{commands}
    """.format(
      plotargs=plot_args.prettyprint(),
      commands=commands.prettyprint()
      ))

    cmd = raw_input('> ').strip().split()

    if len(cmd) < 1:
      continue

    if cmd[0] == 'quit':
      raise StopIteration()

    if cmd[0] == 'set':
      try:
        if len(cmd) == 2:
          plot_args[cmd[1]] = None
        else:
          plot_args[cmd[1]] = " ".join(cmd[2:])
      except IndexError:
        print("'set' requires a variable name and a value")

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
      return plot_args

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
