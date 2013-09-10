import json
import logparser.postprocess.util as util

import logging
logger = logging.getLogger(__name__)


def flatten(args):
  """ Flatten an output file to create tabular data """

  try:
    with open(args.input) as fin:
      data = json.load(fin)
  except Exception as e:
    logger.error("Invalid input file. Expected JSON")
    logger.debug("JSON Error: {0}".format(e))
    raise RuntimeError()
  except IOError as e:
    logger.error("Could not read '{0}'".format(args.input))
    logger.debug("IOError: {0}".format(e))
    raise RuntimeError()

  # Get the first one
  parsers = [data.values()[0].keys()[0]] if args.p is None else args.p

  flattened = util.filter_and_flatten(data, args.f, parsers, label_files=True)

  print(" ".join(flattened.headers))

  for row in flattened.by_row(convert=str):
    print(" ".join(row))
