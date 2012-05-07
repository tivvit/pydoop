# BEGIN_COPYRIGHT
# END_COPYRIGHT

"""
Counts occurrences of IP addresses in Apache access log files,
optionally ignoring IP addresses listed in a given file. The input
directory must contain files formatted as described in:

  http://httpd.apache.org/docs/1.3/logs.html#common

NOTE: the MapReduce application launched by this script is a
      Pydoop reimplementation of a Dumbo programming example from
      K. Bosteels, 'Fuzzy techniques in the usage and construction of
      comparison measures for music objects', PhD thesis, Ghent
      University, 2009, available at http://users.ugent.be/~klbostee.
"""

import sys, os, optparse, operator, subprocess as sp, uuid

import pydoop.hdfs as hdfs
import pydoop.hadoop_utils as hu


HADOOP = hu.get_hadoop_exec()
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_INPUT = os.path.normpath(os.path.join(THIS_DIR, "input"))
LOCAL_MR_SCRIPT = "bin/ipcount.py"
BASE_MR_OPTIONS = {
  "mapred.job.name": "ipcount",
  "mapreduce.admin.user.home.dir": os.path.expanduser("~"),
  "hadoop.pipes.java.recordreader": "true",
  "hadoop.pipes.java.recordwriter": "true",
  }


def build_d_options(opt_dict):
  d_options = []
  for name, value in opt_dict.iteritems():
    d_options.append("-D %s=%s" % (name, value))
  return " ".join(d_options)


def hadoop_pipes(pipes_opts, hadoop=HADOOP):
  p = sp.Popen("%s pipes %s" % (hadoop, pipes_opts), shell=True)
  return os.waitpid(p.pid, 0)[1]


def collect_output(mr_out_dir):
  ip_list = []
  for fn in hdfs.ls(mr_out_dir):
    if hdfs.path.basename(fn).startswith("part"):
      with hdfs.open(fn) as f:
        for line in f:
          ip, count = line.strip().split("\t")
          ip_list.append((ip, int(count)))
  return ip_list


class HelpFormatter(optparse.IndentedHelpFormatter):
  def format_description(self, description):
    return description + "\n" if description else ""


def make_parser():
  parser = optparse.OptionParser(
    usage="%prog [OPTIONS]", formatter=HelpFormatter(),
    )
  parser.set_description(__doc__.lstrip())
  parser.add_option("-i", dest="input", metavar="STRING",
                    help="input dir/file ['%default']", default=DEFAULT_INPUT)
  parser.add_option("-e", dest="exclude_fn", metavar="STRING",
                    help="exclude IPs listed in this file [None]")
  parser.add_option("-n", type="int", dest="n_top", metavar="INT",
                    help="number of top IPs to list [%default]", default=5)
  parser.add_option("-o", dest="output", metavar="STRING",
                    help="output file [stdout]", default=sys.stdout)
  return parser


def main(argv):

  parser = make_parser()
  opt, _ = parser.parse_args(argv)
  if opt.output is not sys.stdout:
    opt.output = open(opt.output, 'w')

  wd = "pydoop_test_ipcount"
  hdfs.mkdir(wd)
  mr_script = hdfs.path.join(wd, os.path.basename(LOCAL_MR_SCRIPT))
  hdfs.put(LOCAL_MR_SCRIPT, mr_script)
  input_ = hdfs.path.join(wd, os.path.basename(opt.input))
  hdfs.put(opt.input, input_)
  output = hdfs.path.join(wd, uuid.uuid4().hex)

  mr_options = BASE_MR_OPTIONS.copy()
  if opt.exclude_fn:
    exclude_bn = os.path.basename(opt.exclude_fn)
    exclude_fn = hdfs.path.join(wd, exclude_bn)
    hdfs.put(opt.exclude_fn, exclude_fn)
    mr_options["mapred.cache.files"] = "%s#%s" % (exclude_fn, exclude_bn)
    mr_options["mapred.create.symlink"] = "yes"
    mr_options["ipcount.excludes"] = exclude_bn
  d_options = build_d_options(mr_options)
  hadoop_pipes("%s -program %s -input %s -output %s" % (
    d_options, mr_script, input_, output
    ))

  ip_list = collect_output(output)
  hdfs.rmr(wd)
  ip_list.sort(key=operator.itemgetter(1), reverse=True)
  if opt.n_top:
    ip_list = ip_list[:opt.n_top]
  for ip, count in ip_list:
    opt.output.write("%s\t%d\n" % (ip, count))

  if opt.output is not sys.stdout:
    opt.output.close()


if __name__ == "__main__":
  main(sys.argv[1:])
