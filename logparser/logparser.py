import os.path
from os.path import join as pathjoin
import progressbar
import json
import sys
from logparser.parsers import available_parsers


def filelen(fname):
  l = 0
  with open(fname) as f:
    for i in xrange(1000):
      s = next(f)
      l += len(s)

  return os.path.getsize(fname) / (l / 1000)


def parse_file(identifier, path):

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

      for parser in parsers:
        if parser.name not in data:
          data[parser.name] = []

        try:
          parsed = parser(line)
          data[parser.name].append(parsed.data)
        except ValueError:
          pass

  bar.finish()

  return data


def main(args):

  parsers = available_parsers()

  datafiles = {}

  for (dirpath, dirnames, files) in os.walk(args.logdir):
    for file in files:
      if file in args.lognames:
        path = pathjoin(dirpath, file)
        identifier = os.path.relpath(path, args.logdir)
        datafiles[identifier] = parse_file(identifier, path)

  if len(datafiles) == 0:
    sys.stderr.write("No files found\n")
    sys.exit(1)

  with open(args.o, 'w') as fout:
    json.dump(datafiles, fout, indent=2)
