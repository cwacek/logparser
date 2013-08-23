from logparser.parsers import Parser

import re
from datetime import datetime
import calendar


class PingBound(Parser):

  name = 'pingbound'

  regex = re.compile(r"\[PingBound\] (Failed.|Passed.).*"
                     "\[lbound: ([0-9.]+), ubound: ([0-9.]+), "
                     "latency: ([0-9.]+)\]")

  _headers = ['time', 'passed', 'lbound', 'ubound', 'latency']

  def __init__(self, line):
    fields = line.split()

    match = self.regex.search(line)
    if not match:
      raise ValueError

    date = datetime.strptime(" ".join(fields[0:3]), "%b %d %H:%M:%S.%f")
    date = date.replace(year=datetime.today().year)

    self.data = {
        'time': calendar.timegm(date.utctimetuple()),
        'passed': 1 if match.group(1) == 'Passed.' else 0,
        'lbound': float(match.group(2)),
        'ubound': float(match.group(3)),
        'latency': float(match.group(4))
    }

  @property
  def data(self):
    return self._data

  @data.setter
  def data(self, d):
    self._data = d

__virtual__ = ('pingbound-old', PingBound)
