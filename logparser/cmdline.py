import argparse
import sys
import core
import string
import postprocess.manip


def run_postprocess_plot(args):
  """ Helper to allow us to fail imports for
      rpy2 only if we're plotting """
  import postprocess.plot
  postprocess.plot.plot(args)


def setup_logging():
  import logging
  logger = logging.getLogger()
  sh = logging.StreamHandler()
  fmt = logging.Formatter("%(asctime)s:%(name)s:%(levelname)s::%(message)s")
  sh.setFormatter(fmt)
  logger.addHandler(sh)
  sh.setLevel(logging.DEBUG)
  logger.setLevel(logging.DEBUG)
  return logger


class ParserOptsAction(argparse.Action):
  def __call__(self, parser, namespace, values, option_string=None):
    name, val = values.split('=')
    if namespace.parser_opts is None:
      namespace.parser_opts = dict()

    if name in namespace.parser_opts:
      namespace.parser_opts[name].append(val)
    else:
      namespace.parser_opts[name] = [val]


def add_parser_args(subp):
  parse_p = subp.add_parser('parse',
                            help="Parse data from a set of files using one "
                                 "or more parsers")
  parse_p.add_argument("-o", help="Output filename",
                       metavar="OUTPUT", required=True)

  parse_p.add_argument("-p", "--parsers", action='append',
                       help="The parsers to use. Will search for them in"
                            "the logparser.parsers namespace."
                       )
  parse_p.add_argument('--parser_opts', action=ParserOptsAction,
                       help="Any parser specific options in "
                            "'parser_name.option=value' "
                            "syntax.",
                       default={})

  parse_p.add_argument('--visual', help='Show visually which lines are parsed',
                       action='store_true')

  parse_p.add_argument('logdir',
                       help="A directory from which to search for logfiles")
  parse_p.add_argument('lognames', nargs='+',
                       help="Names which should be considered log files",
                       default=['log'])
  parse_p.set_defaults(func=core.parse)


def add_list_args(subp):
  parser = subp.add_parser('list', help="List system information")
  parser.add_argument('infotype', choices=['parsers'],
                      help="Information to list")

  parser.add_argument('--parser_opts', action=ParserOptsAction,
                      help="Any parser specific options in "
                           "'parser_name.option=value' "
                           "syntax.",
                      default={})

  parser.set_defaults(func=core.list)


def add_graph_args(subp):
  parser = subp.add_parser('graph', help='Plot using ggplot')

  parser.add_argument('input',
                      help="A file output by 'parse'")

  parser.add_argument('-p',
                      help="Grab data gathered by this parser. If none, "
                           "take the first one seen.",
                      default=None)

  parser.add_argument('-f',
                      help="Filter files to include. '*' will "
                           "glob like the shell",
                      default='*')

  parser.add_argument('-x', help="The expression to put on the X-axis",
                      required=True)
  parser.add_argument('-y', help="The expression to put on the Y-axis",
                      required=True)
  parser.add_argument('-t', '--type',
                      help='Type of plot to make',
                      choices=['lines', 'points', 'boxplot'],
                      default='points')
  parser.add_argument('--facets',
                      help="Split into multiple plots based on this value. "
                           "'file_' is a special value which splits on parsed "
                           "files.")

  parser.set_defaults(func=run_postprocess_plot)


def add_flatten_args(subp):
  parser = subp.add_parser('flatten',
                           help="Transform parsed data into tabular output.")

  parser.add_argument('-p',
                      help="Flatten data from this parser. If not "
                           "provided it will take the first one seen.",
                      default=None)

  parser.add_argument('-f',
                      help="Filter files to include. '*' will "
                           "glob like the shell",
                      default='*')
  parser.add_argument('input',
                      help="A file output by 'parse'")

  parser.set_defaults(func=postprocess.manip.flatten)


def script_run():
  parser = argparse.ArgumentParser()
  subp = parser.add_subparsers()

  add_parser_args(subp)
  add_list_args(subp)
  add_flatten_args(subp)
  add_graph_args(subp)

  args = parser.parse_args()
  logger = setup_logging()
  try:
    args.func(args)
  except RuntimeError as e:
    sys.exit(1)
  except Exception as e:
    logger.error("Fatal exception: {0}".format(e))
    sys.exit(1)

if __name__ == '__main__':
  script_run()
