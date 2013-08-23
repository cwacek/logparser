import os.path
from os.path import join as pathjoin
import progressbar
import json
from logparser.parsers import available_parsers

import logging
logger = logging.getLogger(__name__)


def filelen(fname, sample=10000):

  l = 0
  with open(fname) as f:
    for i in xrange(sample):
      s = next(f)
      l += len(s)

  logger.debug("Calculated expected number of lines as {0}"
               .format(os.path.getsize(fname) / (l / sample)))
  return os.path.getsize(fname) / (l / sample)


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
  logger.debug("Processed {0} lines total".format(ctr))

  for parser, d in data.iteritems():
    if len(d) == 0:
      logger.warn("'{0}' parsed zero datapoints".format(parser))

  return data


def parse(args):

  parsers = dict(((p, available_parsers().get(p)) for p in args.parsers))
  missing_parsers = [p[0] for p in parsers.iteritems() if p[1] is None]

  if len(missing_parsers):
    logger.warn("Unable to load parsers: {0}"
                .format(missing_parsers))
    raise RuntimeError

  datafiles = {}
  processed = 0

  for (dirpath, dirnames, files) in os.walk(args.logdir):
    for file in files:
      if file in args.lognames:
        path = pathjoin(dirpath, file)
        identifier = os.path.relpath(path, args.logdir)
        datafiles[identifier] = parse_file(identifier, path, parsers)
        processed += 1

  if len(datafiles) == 0:
    logger.warn("No files found")
    raise RuntimeError

  with open(args.o, 'w') as fout:
    json.dump(datafiles, fout, indent=2)
