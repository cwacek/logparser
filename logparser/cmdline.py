import argparse
import sys
import core


def setup_logging():
  import logging
  logger = logging.getLogger()
  sh = logging.StreamHandler()
  fmt = logging.Formatter("%(asctime)s:%(name)s:%(levelname)s::%(message)s")
  sh.setFormatter(fmt)
  logger.addHandler(sh)
  sh.setLevel(logging.DEBUG)
  logger.setLevel(logging.DEBUG)


def script_run():
  parser = argparse.ArgumentParser()
  parser.add_argument('logdir',
                      help="A directory from which to search for logfiles")
  parser.add_argument('lognames', nargs='+',
                      help="Names which should be considered log files",
                      default=['log'])
  parser.add_argument("-o", help="Output filename",
                      metavar="OUTPUT", required=True)

  parser.add_argument("-p", "--parsers", action='append',
                      help="The parsers to use. Will search for them in"
                           "the logparser.parsers namespace."
                      )

  args = parser.parse_args()
  setup_logging()
  try:
    core.parse(args)
  except RuntimeError:
    sys.exit(1)

if __name__ == '__main__':
  script_run()
