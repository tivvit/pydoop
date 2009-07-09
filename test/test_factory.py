import unittest
import random

import sys

#----------------------------------------------------------------------------

from pydoop.pipes import Factory, Mapper, Reducer
from pydoop.pipes import RecordReader, RecordWriter
#from pydoop.pipes import Partitioner

import pydoop_pipes
#----------------------------------------------------------------------------

import sys

class mapper(Mapper):
  call_history=[]

  def __init__(self, ctx):
    Mapper.__init__(self)
    mapper.call_history.append('initialized')

  def map(self, ctx):
    mapper.call_history.append('map() invoked')

class reducer(Reducer):
  call_history=[]
  def __init__(self, ctx):
    Reducer.__init__(self)
    reducer.call_history.append('initialized')
  def reduce(self, ctx):
    reducer.call_history.append('reduce() invoked')


class record_reader(RecordReader):
  def __init__(self, ctx):
    RecordReader.__init__(self)
    self.ctx = ctx
    self.counter = 0

  def next(self):
    if self.counter < self.NUMBER_RECORDS:
      self.counter += 1
      return (True, self.KEY_FORMAT % self.counter, self.DEFAULT_VALUE)
    else:
      return (False, '', '')

  def getProgress(self):
    return float(self.counter)/self.NUMBER_RECORDS

#----------------------------------------------------------------------------


class factory_tc(unittest.TestCase):
  def setUp(self):
    self.d = {'input_key' : 'inputkey',
              'input_value' : 'inputvalue',
              'input_split' : 'inputsplit',
              'input_key_class' : 'keyclass',
              'input_value_class' : 'valueclass'}
    self.m_ctx = pydoop_pipes.get_MapContext_object(self.d)
    self.r_ctx = pydoop_pipes.get_ReduceContext_object(self.d)

  def __check_ctx(self):
    self.assertEqual(self.m_ctx.getInputKey(), self.d['input_key'])
    self.assertEqual(self.m_ctx.getInputValue(), self.d['input_value'])
    self.assertEqual(self.m_ctx.getInputSplit(), self.d['input_split'])
    self.assertEqual(self.m_ctx.getInputKeyClass(), self.d['input_key_class'])
    self.assertEqual(self.m_ctx.getInputValueClass(), self.d['input_value_class'])

  def test_factory_costructor(self):
    f = Factory(mapper, reducer)
    self.failUnless(isinstance(f.createMapper(self.m_ctx), mapper))
    self.failUnless(isinstance(f.createReducer(self.r_ctx), reducer))
    #--
    f = Factory(mapper, reducer, record_reader)
    self.failUnless(isinstance(f.createMapper(self.m_ctx), mapper))
    self.failUnless(isinstance(f.createReducer(self.r_ctx), reducer))
    self.failUnless(isinstance(f.createRecordReader(self.m_ctx), record_reader))

  def test_map_reduce_factory(self):
    self.__check_ctx()
    mapper.call_history = []
    reducer.call_history = []
    mf = Factory(mapper, reducer)
    f = pydoop_pipes.TestFactory(mf)
    pydoop_pipes.try_factory_internal(mf)
    self.assertEqual(len(mapper.call_history), 2)
    self.assertEqual(len(reducer.call_history), 2)
    self.failUnless(isinstance(f.createMapper(self.m_ctx), mapper))
    self.failUnless(isinstance(f.createReducer(self.r_ctx), reducer))


#----------------------------------------------------------------------------
def suite():
  suite = unittest.TestSuite()
  #--
  suite.addTest(factory_tc('test_factory_costructor'))
  suite.addTest(factory_tc('test_map_reduce_factory'))
  return suite

if __name__ == '__main__':
  runner = unittest.TextTestRunner(verbosity=2)
  runner.run((suite()))

