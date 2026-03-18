'''
This module is related to translation. Ensuring subtitles are available in various languages.
'''
import os
import argostranslate.package
import argostranslate.translate

from ytffmpeg import getLogger
log = getLogger(__name__)

def parse_srt(srt_path: str) -> list[dict]:
    '''
    Parse an SRT file and return a list of subtitle entries with timing and text.
    Each entry is a dict with: {'index': int, 'start': str, 'end': str, 'text': str}
    '''
    if not os.path.exists(srt_path):
        log.error(f'SRT file not found: {srt_path}')
        return []

    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split into subtitle blocks
    blocks = content.strip().split('\n\n')
    subtitles = []

    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue

        try:
            index = int(lines[0])
            timing = lines[1]
            text = '\n'.join(lines[2:])

            # Parse timing (format: "00:00:00,000 --> 00:00:02,000")
            if ' --> ' in timing:
                start, end = timing.split(' --> ')
                subtitles.append({
                    'index': index,
                    'start': start.strip(),
                    'end': end.strip(),
                    'text': text.strip()
                })
        except (ValueError, IndexError) as e:
            log.warning(f'Skipping malformed subtitle block: {e}')
            continue

    return subtitles

def write_srt(subtitles: list[dict], output_path: str) -> None:
    '''
    Write subtitle entries back to an SRT file.
    '''
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, sub in enumerate(subtitles):
            f.write(f"{sub['index']}\n")
            f.write(f"{sub['start']} --> {sub['end']}\n")
            f.write(f"{sub['text']}\n\n")
    log.info(f'Wrote {len(subtitles)} subtitle entries to {output_path}')

def ensure_translation_package(from_lang: str, to_lang: str) -> bool:
    '''
    Ensure the Argos Translate package for the language pair is installed.
    Returns True if the package is available, False otherwise.
    '''
    # Update package index
    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()

    # Find the required package
    target_package = None
    for pkg in available_packages:
        if pkg.from_code == from_lang and pkg.to_code == to_lang:
            target_package = pkg
            break

    if not target_package:
        log.error(f'No translation package available for {from_lang} -> {to_lang}')
        return False

    # Check if already installed
    installed_packages = argostranslate.package.get_installed_packages()
    for pkg in installed_packages:
        if pkg.from_code == from_lang and pkg.to_code == to_lang:
            log.debug(f'Translation package {from_lang} -> {to_lang} already installed')
            return True

    # Install the package
    log.info(f'Installing translation package {from_lang} -> {to_lang}...')
    try:
        argostranslate.package.install_from_path(target_package.download())
        log.info(f'Successfully installed translation package {from_lang} -> {to_lang}')
        return True
    except Exception as e:
        log.error(f'Failed to install translation package: {e}')
        return False

def translate_text(text: str, from_lang: str, to_lang: str) -> str:
    '''
    Translate text from one language to another using Argos Translate.
    '''
    if from_lang == to_lang:
        return text

    # Ensure translation package is available
    if not ensure_translation_package(from_lang, to_lang):
        log.error(f'Cannot translate {from_lang} -> {to_lang}: missing package')
        return text

    # Get the translation
    try:
        translated = argostranslate.translate.translate(text, from_lang, to_lang)
        return translated
    except Exception as e:
        log.error(f'Translation failed: {e}')
        return text

def split_text_by_word_count(text: str, target_segments: list[dict]) -> list[str]:
    '''
    Split translated text to match the number and approximate length of original segments.
    This preserves timing by distributing words across the same number of subtitle entries.
    '''
    words = text.split()
    total_words = len(words)

    # Calculate how many words each original segment had
    original_word_counts = []
    for seg in target_segments:
        seg_words = len(seg['text'].split())
        original_word_counts.append(seg_words)

    total_original_words = sum(original_word_counts)

    # If we have no words, return empty strings
    if total_words == 0 or total_original_words == 0:
        return [''] * len(target_segments)

    # Distribute translated words proportionally
    result = []
    word_idx = 0

    for i, original_count in enumerate(original_word_counts):
        # Calculate proportional word count for this segment
        if total_original_words > 0:
            proportional_count = int(round(original_count * total_words / total_original_words))
        else:
            proportional_count = 0

        # Ensure we don't exceed available words
        proportional_count = min(proportional_count, total_words - word_idx)

        # For the last segment, use all remaining words
        if i == len(original_word_counts) - 1:
            segment_words = words[word_idx:]
        else:
            segment_words = words[word_idx:word_idx + proportional_count]

        result.append(' '.join(segment_words))
        word_idx += len(segment_words)

    return result

def translate_subtitles(source_srt: str, from_lang: str, to_lang: str) -> str:
    '''
    Translate subtitles from one language to another while preserving timing.

    Strategy:
    1. Parse the source SRT file to extract all text and timings
    2. Combine all text into one document for context-aware translation
    3. Translate the full text to preserve intent and context
    4. Split the translated text back into segments matching original timing
    5. Write new SRT file with translated text and original timings

    Returns the path to the translated SRT file.
    '''
    if from_lang == to_lang:
        log.info(f'Source and target languages are the same ({from_lang}), skipping translation')
        return source_srt

    # Parse source SRT
    log.info(f'Parsing source subtitles from {source_srt}')
    subtitles = parse_srt(source_srt)
    if not subtitles:
        log.error(f'Failed to parse {source_srt}')
        return ''

    # Extract full text for context-aware translation
    full_text = ' '.join([sub['text'] for sub in subtitles])
    log.info(f'Translating {len(full_text)} characters from {from_lang} to {to_lang}...')

    # Translate full text
    translated_text = translate_text(full_text, from_lang, to_lang)
    if not translated_text:
        log.error('Translation failed')
        return ''

    log.info(f'Translation complete: {len(translated_text)} characters')

    # Split translated text to match original segment count
    translated_segments = split_text_by_word_count(translated_text, subtitles)

    # Create new subtitle entries with translated text and original timing
    translated_subtitles = []
    for i, sub in enumerate(subtitles):
        translated_subtitles.append({
            'index': sub['index'],
            'start': sub['start'],
            'end': sub['end'],
            'text': translated_segments[i] if i < len(translated_segments) else ''
        })

    # Write translated SRT
    output_srt = source_srt.replace(f'.{from_lang}.srt', f'.{to_lang}.srt')
    write_srt(translated_subtitles, output_srt)

    return output_srt
