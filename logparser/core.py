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
    try:
      for i in xrange(sample):
        s = next(f)
        l += len(s)
    except StopIteration:
      pass

  logger.debug("Calculated expected number of lines as {0}"
               .format(os.path.getsize(fname) / (l / i)))
  return os.path.getsize(fname) / (l / i)


def parse_file(identifier, path, parsers, highlight=False):
  """ Apply each available parser to a file and return
  the processed output. If :highlight: is set, actually output
  the files with parsed lines highlighted.
  """

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

      line_parsed = False
      for parser_name, parser in parsers.iteritems():
        if parser_name not in data:
          data[parser_name] = []

        try:
          parsed = parser(line)
          data[parser_name].append(parsed.data)
          line_parsed = True
        except ValueError:
          pass

      if highlight:
        if line_parsed:
          print("\033[92m{0}\033[0m".format(line.strip()))
        else:
          print("{0}".format(line.strip()))

  bar.finish()
  logger.debug("Processed {0} lines total".format(ctr))

  for parser, d in data.iteritems():
    if len(d) == 0:
      logger.warn("'{0}' parsed zero datapoints".format(parser))

  return data


def list(args):
  """ List system information """

  if args.infotype == 'parsers':
    for name, parser in available_parsers(args).iteritems():
      print("{0:15} - {1}".format(name, parser.desc))
    return


def parse(args):

  parsers = dict(((p, available_parsers(args).get(p)) for p in args.parsers))

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
        datafiles[identifier] = parse_file(identifier, path,
                                           parsers, highlight=args.visual)
        processed += 1

  if len(datafiles) == 0:
    logger.warn("No files found")
    raise RuntimeError

  with open(args.o, 'w') as fout:
    json.dump(datafiles, fout, indent=2)
