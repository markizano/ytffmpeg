'''
Handles generation and management of metadata associated with a video.
'''
import os
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from ytffmpeg import getLogger, const, utils

log = getLogger(__name__)

LLM = None

GENERATE_TITLE_PROMPT = '''Generate a title.
Based on the subtitles provided, summarize the post in a 1-3 word summary that would be an engaging title.
No markdown or extra formatting accepted.
Just the 1 to 3 word summary.
'''

GENERATE_DESCRIPTION_PROMPT = '''Summarize the video content for the video description.
If the video is short (less than 60 seconds), give a one sentence summary.
If multiple points were described, use bullet points to highlight them.
Markdown is not allowed in descriptions.
Keep it under 5000 characters.
'''

def getClient():
    '''
    Get a connection to the LLM endpoint for dynamically generating title and description as necessary.
    '''
    global LLM
    if LLM is None:
        LLM = init_chat_model(
            model=const.LLM_MODEL,
            model_provider=const.LLM_PROVIDER,
        )
    return LLM

def generateTitle(resource: str) -> str:
    '''
    Generate a title for a video based on the subtitles.
    Reads the text transcript file for the resource and sends its content to the LLM.
    '''
    try:
        txt_path = f'build/{utils.filename(resource)}.txt'

        if not os.path.exists(txt_path):
            log.warning(f'Transcript file {txt_path} not found. Cannot generate title.')
            return ''

        log.info(f'Generating title for \x1b[1m{resource}\x1b[0m from transcript at {txt_path}')

        # Read the transcript file content
        subtitle_content = open(txt_path, 'r', encoding='utf-8').read()

        messages = [
            SystemMessage(content=GENERATE_TITLE_PROMPT),
            HumanMessage(content=subtitle_content)
        ]
        response = getClient().invoke(messages)
        return str(response.content).strip()
    except Exception as e:
        log.error(f'Exception generating title: {e}')
        return ''

def generateDescription(resource: str) -> str:
    '''
    Generate a description for a video based on the subtitles.
    Reads the text transcript file for the resource and sends its content to the LLM.
    '''
    try:
        txt_path = f'build/{utils.filename(resource)}.txt'

        if not os.path.exists(txt_path):
            log.warning(f'Transcript file {txt_path} not found. Cannot generate description.')
            return ''

        log.info(f'Generating description for \x1b[1m{resource}\x1b[0m from transcript at {txt_path}')

        # Read the transcript file content
        subtitle_content = open(txt_path, 'r', encoding='utf-8').read()

        messages = [
            SystemMessage(content=GENERATE_DESCRIPTION_PROMPT),
            HumanMessage(content=subtitle_content)
        ]
        response = getClient().invoke(messages)
        return str(response.content).strip()
    except Exception as e:
        log.error(f'Exception generating description: {e}')
        return ''
