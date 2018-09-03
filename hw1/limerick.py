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
    
    def _is_suffix(self, suffix_a, suffix_b):
      """
      Return True if either suffix_a is a suffix of suffix_b, vice versa, or the two 
      suffixes are the same. Return False otherwise.
      """
      is_suffix = False
      if len(suffix_a) == 0 or len(suffix_b) == 0: is_suffix = False
      elif suffix_a == suffix_b: is_suffix = True
      elif len(suffix_a) > len(suffix_b):
        is_suffix = suffix_b == suffix_a[len(suffix_a) - len(suffix_b):]
      else:
        is_suffix = suffix_a == suffix_b[len(suffix_b) - len(suffix_a):]
      return is_suffix

    def rhymes(self, a, b):
        """
        Returns True if two words (represented as lower-case strings) rhyme,
        False otherwise.
        """
        a_suffix_list = self._get_suffix_list(a.lower())
        b_suffix_list = self._get_suffix_list(b.lower())
        for suffix_a in a_suffix_list:
          for suffix_b in b_suffix_list:
            if self._is_suffix(suffix_a, suffix_b):
                return True
        return False

    def _get_lines(self, text):
      """
      Split the text into A lines and B lines and return the resulting lists as tuple.
      """
      lines = text.split('\n')
      lines = [line for line in lines if line.strip()] # ignore any empty lines
      a_lines = []
      b_lines = []
      for index, line in enumerate(lines):
        if index in [0, 1, 4]:
          a_lines.append(line)
        else:
          b_lines.append(line)
      a_lines =[self._remove_punctuations(line) for line in a_lines]
      b_lines =[self._remove_punctuations(line) for line in b_lines]
      return a_lines, b_lines

    def _is_valid_diff(self, a_num_syllables, b_num_syllables):
      """
      Return True if the inter-line syllable count difference conforms to the 
      assignment specification. Return False otherwise.
      """
      # The syllable count difference between the B lines must not be greater than 2
      if abs(b_num_syllables[0] - b_num_syllables[1]) > 2: return False 

      # The syllable count difference between any of the A lines must not be greater
      # than 2
      for i in range(len(a_num_syllables)):
        for j in range(len(a_num_syllables)):
          if abs(a_num_syllables[i] - a_num_syllables[j]) > 2: return False

      # Each of the B lines should have fewer syllables than the A lines
      for i in range(len(a_num_syllables)):
        for j in range(len(b_num_syllables)):
           if a_num_syllables[i] - b_num_syllables[j] <= 0: return False
      return True
      

    def _lines_do_rhyme(self, lines):
      """
      Return True if all the lines rhyme with each other. Return False otherwise.
      """
      do_rhyme = True
      for i in range(len(lines)):
        for j in range(len(lines)):
          i_terminal_word = word_tokenize(lines[i])[-1]
          j_terminal_word = word_tokenize(lines[j])[-1]
          do_rhyme = do_rhyme and self.rhymes(i_terminal_word, j_terminal_word)
      return do_rhyme
    
    def _line_num_syllables(self, line):
      """
      Return the number of syllables in line.
      """
      return sum([self.num_syllables(word) for word in word_tokenize(line)])

    def _remove_punctuations(self, raw):
      """
      Remove punctuations from raw text.
      """
      return raw.translate(None, punctuation)


    def is_limerick(self, text):
        """
        Takes text where lines are separated by newline characters.  Returns
        True if the text is a limerick, False otherwise.

        A limerick is defined as a poem with the form AABBA, where the A lines
        rhyme with each other, the B lines rhyme with each other, and the A lines do not
        rhyme with the B lines.


        Additionally, the following syllable constraints should be observed:
          DONE * No two A lines should differ in their number of syllables by more than two.
          DONE * The B lines should differ in their number of syllables by no more than two.
          DONE * Each of the B lines should have fewer syllables than each of the A lines.
          DONE * No line should have fewer than 4 syllables

        (English professors may disagree with this definition, but that's what
        we're using here.)
        """
        # Check if the text should be considered as a limerick to begin with
        a_lines, b_lines = self._get_lines(text)
        if (len(a_lines) + len(b_lines) != 5): return False
        if not (len(a_lines) == 3 and len(b_lines) == 2): return False

        # check line-level syllable count
        a_num_syllables = [self._line_num_syllables(line) for line in a_lines]
        b_num_syllables = [self._line_num_syllables(line) for line in b_lines]
        if sum(a_num_syllables) < 4 or sum(b_num_syllables) < 4: return False

        # check inter-line level syllable count difference
        if not self._is_valid_diff(a_num_syllables, b_num_syllables): return False
  
        # All A lines must rhyme with each other
        if not self._lines_do_rhyme(a_lines): return False 
        
        # All B lines must rhyme with each other
        if not self._lines_do_rhyme(b_lines): return False 
       
        # A lines and B lines must not rhyme with each other 
        a_lines.extend(b_lines)
        if self._lines_do_rhyme(a_lines): return False 
        
        # All constraints have been addressed; assume the text is a limerick
        return True 


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