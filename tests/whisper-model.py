#!/usr/bin/env python3

import os
from kizano import getLogger
from faster_whisper import WhisperModel
log = getLogger('transcribe')

log.info('Loading model...')
model = WhisperModel(os.getenv('WHISPER_MODEL', 'guillaumekln/faster-whisper-large-v2'), device='cuda', compute_type='auto')
log.info('Model loaded!')
args = {
    'word_timestamps': True,
    'language': os.getenv('LANGUAGE', 'en'),
}
log.info('Transcribing...')
transcript, tinfo = model.transcribe('resources/longer-test.m4a', **args)
log.debug(tinfo)
for word in transcript:
    log.debug(word.text)

log.info('Complete!')
