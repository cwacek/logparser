import argparse
import logparser

if __name__ == '__main__':
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
  logparser.logparser.main(args)
