Custom Parsers and Loading
===========================

Parsers are loaded in one of two ways. The second method is more
complicated, but actually takes precedence:

1. __parser__ method

    A module can define a single parser by providing a
    __parser__ definition for the parser. This should be
    a tuple containing the name of the parser and a
    callable as described above.

        class ExampleParser(logparser.parsers.Parser):

            _name = 'example_parser'
            _desc = 'An example'
            _headers = ('datapoint1', 'datapoint2')

            def init(self, line):
                if 'special_string' in line.split():
                      self.data = {
                          'datapoint1': line[0],
                          'datapoint2': line[1]
                      }
                else:
                    raise ValueError()

        __parser__ = ('example_parser', ExampleParser)

2. __loader__ method

    If a package has a method called __loader__, it will
    be called as a generator and passed a set of global
    options. Each iteration should return tuples containing
    names and parser callables.

       def parser1(line):
           raise ValueError

       parser1.name = 'p1'
       parser1.desc = 'A function parser'

       def parser2(line):
           if line[0] =='A':
               return {
                   'name': 'parser2',
                   'data': 'A', 
                   'headers': ['first_letter']
               }
           else:
               raise ValueError
       parser2.name = 'p1'
       parser2.desc = 'A function parser'

       def __loader__(opts):
           for i, parser in enumerate(parser1, parser2):
               yield ("function_parser_{0}".format(i), parser)
