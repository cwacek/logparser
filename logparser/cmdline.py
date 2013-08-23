import argparse
import sys
import core
import postprocess


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


def add_parser_args(subp):
  parse_p = subp.add_parser('parse')
  parse_p.add_argument("-o", help="Output filename",
                       metavar="OUTPUT", required=True)

  parse_p.add_argument("-p", "--parsers", action='append',
                       help="The parsers to use. Will search for them in"
                            "the logparser.parsers namespace."
                       )
  parse_p.add_argument('logdir',
                       help="A directory from which to search for logfiles")
  parse_p.add_argument('lognames', nargs='+',
                       help="Names which should be considered log files",
                       default=['log'])
  parse_p.set_defaults(func=core.parse)


def add_flatten_args(subp):
  parser = subp.add_parser('flatten')

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

  parser.set_defaults(func=postprocess.flatten)


def script_run():
  parser = argparse.ArgumentParser()
  subp = parser.add_subparsers()

  add_parser_args(subp)
  add_flatten_args(subp)

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
