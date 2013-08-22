from operator import itemgetter
import os.path
from os.path import join as pathjoin
import progressbar
import json
from logparser.parsers import available_parsers

import logging
logger = logging.getLogger(__name__)


def filelen(fname):
  l = 0
  with open(fname) as f:
    for i in xrange(1000):
      s = next(f)
      l += len(s)

  return os.path.getsize(fname) / (l / 1000)


def parse_file(identifier, path, parsers):

  lines = filelen(path)
  bar = progressbar.ProgressBar(maxval=lines,
                                widgets=[
                                    '%s ' % identifier,
                                    progressbar.Bar('=', '[', ']'),
                                    ' ',
                                    progressbar.Percentage()
                                ])

  data = dict()
  with open(path) as fin:
    bar.start()
    ctr = 0
    for line in fin:
      if ctr <= lines:
        bar.update(ctr)
      ctr += 1

      for parser_name, parser in parsers.iteritems():
        if parser_name not in data:
          data[parser_name] = []

        try:
          parsed = parser(line)
          data[parser_name].append(parsed.data)
        except ValueError:
          pass

  bar.finish()

  return data


def parse(args):

  parsers = available_parsers()

  missing_parsers = set(args.parsers) - set(parsers.keys())
  if len(missing_parsers):
    logger.warn("Unable to load parsers: {0}"
                .format(map(itemgetter(0), missing_parsers)))
    raise RuntimeError

  datafiles = {}

  for (dirpath, dirnames, files) in os.walk(args.logdir):
    for file in files:
      if file in args.lognames:
        path = pathjoin(dirpath, file)
        identifier = os.path.relpath(path, args.logdir)
        datafiles[identifier] = parse_file(identifier, path, parsers)

  if len(datafiles) == 0:
    logger.warn("No files found")
    raise RuntimeError

  with open(args.o, 'w') as fout:
    json.dump(datafiles, fout, indent=2)
