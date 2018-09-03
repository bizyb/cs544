#!/usr/bin/env python
import argparse
import sys
import codecs
if sys.version_info[0] == 2:
  from itertools import izip
else:
  izip = zip
from collections import defaultdict as dd
import re
import os.path
import gzip
import tempfile
import shutil
import atexit
import re
# Use word_tokenize to split raw text into words
from string import punctuation

import nltk
from nltk.tokenize import word_tokenize



scriptdir = os.path.dirname(os.path.abspath(__file__))


reader = codecs.getreader('utf8')
writer = codecs.getwriter('utf8')


def prepfile(fh, code):
  if type(fh) is str:
    fh = open(fh, code)
  ret = gzip.open(fh.name, code if code.endswith("t") else code+"t") if fh.name.endswith(".gz") else fh
  if sys.version_info[0] == 2:
    if code.startswith('r'):
      ret = reader(fh)
    elif code.startswith('w'):
      ret = writer(fh)
    else:
      sys.stderr.write("I didn't understand code "+code+"\n")
      sys.exit(1)
  return ret

def addonoffarg(parser, arg, dest=None, default=True, help="TODO"):
  ''' add the switches --arg and --no-arg that set parser.arg to true/false, respectively'''
  group = parser.add_mutually_exclusive_group()
  dest = arg if dest is None else dest
  group.add_argument('--%s' % arg, dest=dest, action='store_true', default=default, help=help)
  group.add_argument('--no-%s' % arg, dest=dest, action='store_false', default=default, help="See --%s" % arg)



class LimerickDetector:

    def __init__(self):
        """
        Initializes the object to have a pronunciation dictionary available
        """
        self._pronunciations = nltk.corpus.cmudict.dict()


    def num_syllables(self, word):
        """
        Returns the number of syllables in a word.  If there's more than one
        pronunciation, take the shorter one.  If there is no entry in the
        dictionary, return 1.
        """

        pron_list = self._pronunciations.get(word)
        if not pron_list:
          return 1
        count_list = []
        count = 0
        for pron in pron_list:
          for letter_set in pron:
            if re.findall("\d+", letter_set):
              count += 1
          count_list.append(count)
          count = 0
        return min(count_list)

    def _get_suffix_list(self, word):
      """
      Return the suffix set for word after removing the initial consonant sound from each 
      pronounciation, where applicable. If initial sounds is a vowel sound, do not modify the 
      pronounciation list.
      """
      pron_list = self._pronunciations.get(word)
      suffix_list = []
      if pron_list:
        for pron in pron_list:
          if not re.findall("\d+", pron[0]):
            suffix_list.append(pron[1:])
          else:
            suffix_list.append(pron)
      return suffix_list

    def rhymes(self, a, b):
        """
        Returns True if two words (represented as lower-case strings) rhyme,
        False otherwise.
        """
        a_suffix_list = self._get_suffix_list(a.lower())
        # b_suffix_list = self.__get_suffix_list(b.lower())
        # for a_suffix in a_suffix_list:
        #   for b_suffix in b_suffix_list:
        #     if self.__is_suffix(a_suffix, b_suffix):
        #       if self.__do_rhyme(a_suffix, b_suffix):
        #         return True
        return False

    def is_limerick(self, text):
        """
        Takes text where lines are separated by newline characters.  Returns
        True if the text is a limerick, False otherwise.

        A limerick is defined as a poem with the form AABBA, where the A lines
        rhyme with each other, the B lines rhyme with each other, and the A lines do not
        rhyme with the B lines.


        Additionally, the following syllable constraints should be observed:
          * No two A lines should differ in their number of syllables by more than two.
          * The B lines should differ in their number of syllables by no more than two.
          * Each of the B lines should have fewer syllables than each of the A lines.
          * No line should have fewer than 4 syllables

        (English professors may disagree with this definition, but that's what
        we're using here.)


        """
        # TODO: provide an implementation!
        return False
    # TODO: if implementing guess_syllables add that function here by uncommenting the stub code and
    # completing the function. If you want guess_syllables to be used by num_syllables, feel free to integrate it appropriately.
    #
    # def guess_syllables(self, word):
    #   """
    #   Guesses the number of syllables in a word. Extra credit function.
    #   """
    #   # TODO: provide an implementation!
    #   pass

    # TODO: if composing your own limerick, put it here and uncomment this function. is_limerick(my_limerick()) should be True
    #
    #
    # def my_limerick(self):
    #   """
    #   A limerick I wrote about computational linguistics
    #   """
    #   limerick="""
    #     Replace these words
    #     with your limerick
    #     and then test it out
    #   """
    #   return limerick


# The code below should not need to be modified
def main():
  parser = argparse.ArgumentParser(description="limerick detector. Given a file containing a poem, indicate whether that poem is a limerick or not",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  addonoffarg(parser, 'debug', help="debug mode", default=False)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")




  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  infile = prepfile(args.infile, 'r')
  outfile = prepfile(args.outfile, 'w')

  ld = LimerickDetector()
  lines = ''.join(infile.readlines())
  outfile.write("{}\n-----------\n{}\n".format(lines.strip(), ld.is_limerick(lines)))

if __name__ == '__main__':
  main()