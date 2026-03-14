'''
Constants that can be imported thru the project for a central place to soft configure ytffmpeg.
'''

import os

'Supported Languages'
LANGS = ["auto","af","am","ar","as","az","ba","be","bg","bn","bo","br","bs","ca",
"cs","cy","da","de","el","en","es","et","eu","fa","fi","fo","fr","gl","gu","ha",
"haw","he","hi","hr","ht","hu","hy","id","is","it","ja","jw","ka","kk","km","kn",
"ko","la","lb","ln","lo","lt","lv","mg","mi","mk","ml","mn","mr","ms","mt","my",
"ne","nl","nn","no","oc","pa","pl","ps","pt","ro","ru","sa","sd","si","sk","sl",
"sn","so","sq","sr","su","sv","sw","ta","te","tg","th","tk","tl","tr","tt","uk",
"ur","uz","vi","yi","yo","zh"]

'The LLM model to request when talking to Open WebUI'
LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-oss:20b')

'The LLM provider to use. Default to OpenWebUI as configured, but could be other API endpoints.'
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'ollama')

# Generate a key from AI Studio: https://aistudio.google.com/app/api-keys
'Google API key generated from AI Studio'
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") # If it's set, great, if not, it will be picked up by config.

'Gemini Image Model to use for image generation.'
IMAGE_MODEL_ID = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
