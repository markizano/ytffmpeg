'''
Attempts to load a `ytffmpeg.yml` configuration and validate it against the schema.
Sample confifgs are loaded from `tests/fixtures/configs/*.yml` and asserted against the schema.
'''

import os
import unittest
from jsonschema import validate
import yaml, json

from kizano import getLogger
log = getLogger(__name__)

class TestYtffmpegConfig(unittest.TestCase):

    def setUp(self):
        self.schema = json.load(open('lib/ytffmpeg/schema.json'))
        log.info(self.schema)

    def test_baseConfig(self):
        '''
        Test the base configuration.
        '''
        config = yaml.safe_load(open('tests/fixtures/configs/base.yml'))
        self.assertIsNone(validate(config, self.schema), 'Base configuration failed validation!')

    def test_extendedConfig(self):
        '''
        Test the extended configuration.
        '''
        config = yaml.safe_load(open('tests/fixtures/configs/extended.yml'))
        self.assertIsNone(validate(config, self.schema), 'Extended configuration failed validation!')

    def test_metadataConfig(self):
        '''
        Test the metadata configuration.
        '''
        config = yaml.safe_load(open('tests/fixtures/configs/metadata.yml'))
        self.assertIsNone(validate(config, self.schema), 'Metadata configuration failed validation!')
    
    def test_simpleFilterComplex(self):
        '''
        Test the simple filter complex configuration.
        '''
        config = yaml.safe_load(open('tests/fixtures/configs/simple-filter-complex.yml'))
        self.assertIsNone(validate(config, self.schema), 'Simple filter complex configuration failed validation!')
    
    def test_extendedFilterComplex(self):
        '''
        Test the extended filter complex configuration.
        '''
        config = yaml.safe_load(open('tests/fixtures/configs/extended-filter-complex.yml'))
        self.assertIsNone(validate(config, self.schema), 'Extended filter complex configuration failed validation!')