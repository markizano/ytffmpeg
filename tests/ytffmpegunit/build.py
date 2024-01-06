
import unittest
from ytffmpeg import filter_complex

class TestFilterComplexUnit(unittest.TestCase):

    def test_construct_fullString(self):
        '''
        Assert a full string as argument to FilterComplexFunctionUnit
        '''
        unit = filter_complex.FilterComplexFunctionUnit('fade=in:st=0:d=4.5:alpha=1')
        self.assertEqual(unit.name, 'fade', 'Name should be fade!')
        self.assertEqual(unit.args, ['in'], 'Args should have "in"!')
        self.assertEqual(unit.kwargs, {'st': '0', 'd': '4.5', 'alpha': '1'}, 'Kwargs should have st=0:d=4.5:alpha=1!')

    def test_construct_withFunction(self):
        '''
        Assert a full string as argument to FilterComplexFunctionUnit
        '''
        unit = filter_complex.FilterComplexFunctionUnit("overlay=10:10:enable='between(t,0,5)'")
        self.assertEqual(unit.name, 'overlay', 'Name should be overlay!')
        self.assertEqual(unit.args, ['10', '10'], 'Args should have "10" and "10"!')
        self.assertEqual(unit.kwargs, {'enable': "'between(t,0,5)'"}, "Kwargs should have enable='between(t,0,5)' with quotes included!")

    def test_construct_withSingleArgsKwargs(self):
        '''
        Assert the various types of creating a new instance of FilterComplexFunctionUnit
        '''
        unit = filter_complex.FilterComplexFunctionUnit('fade', 'in:st=0:d=4.5:alpha=1')
        self.assertEqual(unit.name, 'fade', 'Name should be fade!')
        self.assertEqual(unit.args, ['in'], 'Args should have "in"!')
        self.assertEqual(unit.kwargs, {'st': '0', 'd': '4.5', 'alpha': '1'}, 'Kwargs should have st=0:d=4.5:alpha=1!')

    def test_construct_asString(self):
        '''
        Assert the various types of creating a new instance of FilterComplexFunctionUnit
        '''
        unit = filter_complex.FilterComplexFunctionUnit('trim', 'start=1.15:end=4.5')
        self.assertEqual(unit.name, 'trim', 'Name should be trim!')
        self.assertEqual(unit.args, [], 'Args should be empty!')
        self.assertEqual(unit.kwargs, {'start': '1.15', 'end': '4.5'}, 'Kwargs should be start=1.15:end=4.5!')

    def test_construct_asArray(self):
        '''
        Assert the various types of creating a new instance of FilterComplexFunctionUnit
        '''
        unit = filter_complex.FilterComplexFunctionUnit('trim', ['start=1.15', 'end=4.5'])
        self.assertEqual(unit.name, 'trim', 'Name should be trim!')
        self.assertEqual(unit.args, [], 'Args should be empty!')
        self.assertEqual(unit.kwargs, {'start': '1.15', 'end': '4.5'}, 'Kwargs should be start=1.15:end=4.5!')

    def test_construct_asDict(self):
        '''
        Assert the various types of creating a new instance of FilterComplexFunctionUnit
        '''
        unit = filter_complex.FilterComplexFunctionUnit('trim', {'start': '1.15', 'end': '4.5'})
        self.assertEqual(unit.name, 'trim', 'Name should be trim!')
        self.assertEqual(unit.args, [], 'Args should be empty!')
        self.assertEqual(unit.kwargs, {'start': '1.15', 'end': '4.5'}, 'Kwargs should be start=1.15:end=4.5!')

    def test_setattr_asArgString(self):
        '''
        Assert that when we try to set the args or kwargs, they are broken down accordingly.
        So assigning "start=1.15:end=4.5" to args should result in kwargs being {'start': '1.15', 'end': '4.5'}
        If we assign "1024:768:0:0" to args or kwargs, it should result in args = ['1024', '768', '0', '0']
        '''
        unit = filter_complex.FilterComplexFunctionUnit('trim', 'start=1.15:end=4.5')
        unit.args = 'start=1.15:end=4.5'
        self.assertEqual(unit.args, [], 'Args should be empty!')
        self.assertEqual(unit.kwargs, {'start': '1.15', 'end': '4.5'}, 'Kwargs should be start=1.15:end=4.5!')

    def test_setattr_asArgArray(self):
        '''
        '''
        unit = filter_complex.FilterComplexFunctionUnit('trim', 'start=1.15:end=4.5')
        unit.args = ['start=1.15', 'end=4.5']
        self.assertEqual(unit.args, [], 'Args should be empty!')
        self.assertEqual(unit.kwargs, {'start': '1.15', 'end': '4.5'}, 'Kwargs should be start=1.15:end=4.5!')

    def test_setattr_asArgDict(self):
        '''
        Asserts that when we assign a dictionary to args, it is assigned as is.
        '''
        unit = filter_complex.FilterComplexFunctionUnit('trim', 'start=1.15:end=4.5')
        unit.args = {'start': '1.15', 'end': '4.5'}
        self.assertEqual(unit.args, [], 'Args should be empty!')
        self.assertEqual(unit.kwargs, {'start': '1.15', 'end': '4.5'}, 'Kwargs should be start=1.15:end=4.5!')

    def test_setattr_asKwargString(self):
        '''
        '''
        unit = filter_complex.FilterComplexFunctionUnit('trim', 'start=1.15:end=4.5')
        unit.kwargs = 'start=1.15:end=4.5'
        self.assertEqual(unit.args, [], 'Args should be empty!')
        self.assertEqual(unit.kwargs, {'start': '1.15', 'end': '4.5'}, 'Kwargs should be start=1.15:end=4.5!')

    def test_setattr_asKwargArray(self):
        '''
        '''
        unit = filter_complex.FilterComplexFunctionUnit('trim', 'start=1.15:end=4.5')
        unit.kwargs = ['start=1.15', 'end=4.5']
        self.assertEqual(unit.args, [], 'Args should be empty!')
        self.assertEqual(unit.kwargs, {'start': '1.15', 'end': '4.5'}, 'Kwargs should be start=1.15:end=4.5!')


    def test_setattr_asKwargDict(self):
        '''
        Asserts that when we assign a dictionary to kwargs, it is assigned as is.
        '''
        unit = filter_complex.FilterComplexFunctionUnit('trim', 'start=1.15:end=4.5')
        unit.kwargs = {'start': '1.15', 'end': '4.5'}
        self.assertEqual(unit.args, [], 'Args should be empty!')
        self.assertEqual(unit.kwargs, {'start': '1.15', 'end': '4.5'}, 'Kwargs should be start=1.15:end=4.5!')
