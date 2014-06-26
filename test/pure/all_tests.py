# BEGIN_COPYRIGHT
#
# Copyright 2009-2014 CRS4.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# END_COPYRIGHT

import unittest, imp


TEST_MODULE_NAMES = [
  'test_binary_streams',
  'test_framework',
  'test_serialize',
  'test_streams',
  'test_support',
  'test_text_stream',
  'test_utils',
  ]


def suite():
  suites = []
  for name in TEST_MODULE_NAMES:
    fp, pathname, description = imp.find_module(name)
    try:
      module = imp.load_module(name, fp, pathname, description)
      suites.append(module.suite())
    finally:
      fp.close()
  return unittest.TestSuite(tuple(suites))


if __name__ == '__main__':
  import sys
  result = unittest.TextTestRunner(verbosity=2).run(suite())
  sys.exit(not result.wasSuccessful())
