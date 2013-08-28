logparser
=========

A framework for parsing data out of log files, then manipulating
or plotting that data.

Stop writing boilerplate
------------------------

If you spend much time looking through logfiles for data (and I
do), then you know there's the same boilerplate code you write
every time you parse a new file.

This is a framework intended to allow you to stop doing that by
separating the notion of *parsers* from the process of reading
files and aggregating data. To be able to read a new file, you
simply implement a parser and put it somewhere `logparser` can
pick it up.

Install
-------

Simply `python setup.py install`. If you want to use the graphing
functions, you need R and the python rpy2 package.

Parser Framework
----------------

Parsers are designed to be modular, so they're simply callable
objects with a couple of attributes. Parsers are searched for in
the `logparser.parserse namespace. A `parser' is considered to be
any callable which given a string returns a dictionary of data
parsed from it or raises a ValueError if the line doesn't contain
relevant data.

Since parsers are just callables, it's perfectly reasonable to
have them be methods on an instance. The same instance will
then be used on each line, allowing complicated parsers which
save state to be used. An explanation for how to build custom parsers is in the
logparser/parsers directory.

However, even that's too much boilerplate for most things, so
there's a built-in regular expression based parser called
SimpleRegex. This allows simple parsers (i.e. ones without any
state between lines) to be defined as YAML objects. For speed
(and trust me, it matters) regular expressions are applied using
`match`, so they always begin at the beginning of a line.

For example, a parser to read all failed password attempts from
/var/log/auth.log could be defined as follows:

    ---
    - name: failed_attempts
      desc: Parses failed login attempts from auth.log
      regex: '([A-Za-z]+\s\d+\s\d{2}:}:\d{2})\s([a-z\.]+)\sshd.*: Failed password for ([0-9A-Za-z\s]+) from (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
      fields:
        - name: timestamp
          type: time
          fmt: '%b %d %H:%M:%S'
        - name: target_hostname
          type: str
        - name: username
          type: str
        - name: source
          type: str


SimpleRegex loads all regular expression parsers from YAML files
in the logparser.parsers.simple resource directory. You can also
specify any other directory by supplying it on the command line
through the parser option 'simpleregex.files'.  To test if a
custom file is loading, you can use the list command:

    $ # Assume the parser we just defined is in /tmp/authparser
    $ logparser list parsers --parser_opts 'simpleregex.files=/tmp/authparser'
    failed_attempts - Parses failed login attempts from auth.log

We can run it on an actual file too:

    $ logparser parse --parser_opts simpleregex.files=/tmp/authparser -p failed_attempts -o /tmp/out /tmp auth.log
    auth.log [=============================================================================] 100%

