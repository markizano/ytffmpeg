
import unittest
from ytffmpeg import filter_complex

class TestFilterComplexStream(unittest.TestCase):

    def test_construct_asString(self):
        '''
        Assert that we can construct a FilterComplexStream object with a string as primary argument.
        '''
        expectedFuncs = filter_complex.FilterComplexFunctionList([
            filter_complex.FilterComplexFunctionUnit('trim', 'start=1:end=5'),
            filter_complex.FilterComplexFunctionUnit('setpts', 'PTS-STARTPTS')
        ])
        stream = filter_complex.FilterComplexStream(['0:v'], ['video'], expectedFuncs)
        self.assertEqual(stream.istreams, ['0:v'], 'Input should be a stream set to 0:v')
        self.assertEqual(stream.ostreams, ['video'], 'Output should be a stream set to "video"')
        self.assertEqual(stream.functions, expectedFuncs, 'Functions should be set with trim() and setpts().')
        actual = str(stream)
        expected = '[0:v] trim=start=1:end=5,setpts=PTS-STARTPTS [video]'
        self.assertEqual(actual, expected, 'String representation should be as expected.')

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

    def test_construct_asSelf(self):
        '''
        Assert the various types of creating a new instance of FilterComplexFunctionUnit
        '''
        unit = filter_complex.FilterComplexFunctionUnit('trim=start=0:end=5')
        canabalist = filter_complex.FilterComplexFunctionUnit(unit)
        self.assertEqual(canabalist.name, 'trim', 'Name should be trim!')
        self.assertEqual(canabalist.args, [], 'Args should be empty!')
        self.assertEqual(canabalist.kwargs, {'start': '0', 'end': '5'}, 'Kwargs should be start=0:end=5!')

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
