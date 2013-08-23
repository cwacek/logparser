import json
import sys
import fnmatch


def flatten(args):
  """ Flatten an output file to create tabular data """

  try:
    with open(args.input) as fin:
      data = json.load(fin)
  except json.error:
    raise Exception("Invalid input file. Expected JSON")
  except IOError as e:
    raise Exception("Could not read '{0}' [{1}]".format(args.input, e))

  parser = args.p
  headerfields = None

  sys.stderr.write("Processed: ")
  for fname in fnmatch.filter(data.iterkeys(), args.f):
    sys.stderr.write("{0} ".format(fname))
    if parser is None:
      parser = data[fname].keys()[0]

    if headerfields is None:
      headerfields = [key
                      for key, val in data[fname][parser][0].iteritems()
                      if isinstance(val, (float, int, basestring))]
      print(" ".join(headerfields))

    for datapoint in data[fname][parser]:
      buf = " ".join([str(datapoint[h]) for h in headerfields])
      print(buf)

  sys.stderr.write("\n")
