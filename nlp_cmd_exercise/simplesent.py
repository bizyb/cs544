#!/usr/bin/env python3
# by Jon May (jonmay@isi.edu)
# classify a sentence based on if it has more positive or negative words
# do lowercase normalizing

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

def main():
  parser = argparse.ArgumentParser(description="classify a sentence based on if it has more positive or negative words",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  addonoffarg(parser, 'debug', help="debug mode", default=False)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file")
  parser.add_argument("--posfile", "-p", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="pos file")
  parser.add_argument("--negfile", "-n", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="neg file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")
  parser.add_argument("--default", default="pos", help="default category")



  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  workdir = tempfile.mkdtemp(prefix=os.path.basename(__file__), dir=os.getenv('TMPDIR', '/tmp'))

  def cleanwork():
    shutil.rmtree(workdir, ignore_errors=True)
  if args.debug:
    print(workdir)
  else:
    atexit.register(cleanwork)


  infile = prepfile(args.infile, 'r')
  outfile = prepfile(args.outfile, 'w')

  posfile = prepfile(args.posfile, 'r')
  negfile = prepfile(args.negfile, 'r')

  pos = set()
  neg = set()
  for line in posfile:
    pos.add(line.strip())
  for line in negfile:
    neg.add(line.strip())

  for line in infile:
    poscount = 0
    negcount = 0
    for word in line.strip().split():
      word = word.lower()
      if word in pos:
        poscount+=1
      elif word in neg:
        negcount+=1
    if poscount > negcount:
      outfile.write("pos\n")
    elif negcount > poscount:
      outfile.write("neg\n")
    else:
      outfile.write(args.default+"\n")

if __name__ == '__main__':
  main()
