# TODO move to kython?
def cwd_import(name: str):
    import os, sys, importlib
    sys.path.append(os.getcwd())
    res = importlib.import_module(name)
    sys.path.pop()
    return res

config = cwd_import('config')

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WereYouHere")

import inspect
import os.path
from typing import List, Tuple

from .common import Entry, Visit, History, simple_history, Filter, make_filter
from .render import render


def main():
    chrome_dir = config.CHROME_HISTORY_DB_DIR
    takeout_dir = config.GOOGLE_TAKEOUT_DIR
    custom_extractors = config.CUSTOM_EXTRACTORS
    output_dir = config.OUTPUT_DIR
    filters = [make_filter(f) for f in config.FILTERS]
    for f in filters:
        History.add_filter(f) # meh..

    if output_dir is None or not os.path.lexists(output_dir):
        raise ValueError("Expecting OUTPUT_DIR to be set to a correct path!")

    all_histories = []

    def log_hists(histories: List[History], from_: str):
        lengths = [len(h) for h in histories]
        logger.info(f"Got {len(histories)} Histories from {from_}: {lengths}")

    if chrome_dir is not None:
        import wereyouhere.generator.chrome as chrome_gen
        chrome_histories = list(chrome_gen.iter_chrome_histories(chrome_dir))
        all_histories.extend(chrome_histories)
        log_hists(chrome_histories, 'Chrome')
    else:
        logger.warning("CHROME_HISTORY_DB_DIR is not set, not using chrome entries to populate extension DB!")

    if takeout_dir is not None:
        import wereyouhere.generator.takeout as takeout_gen
        takeout_histories = list(takeout_gen.get_takeout_histories(takeout_dir))
        all_histories.extend(takeout_histories)
        log_hists(takeout_histories, 'Google Takeout')
    else:
        logger.warning("GOOGLE_TAKEOUT_DIR is not set, not using Google Takeout for populating extension DB!")

    from wereyouhere.generator import plaintext

    for tag, extractor in custom_extractors:
        import wereyouhere.generator.custom as custom_gen
        logger.info(f"Running extractor {extractor} (tag {tag})")
        custom_histories: List[History]
        if isinstance(extractor, str): # must be shell command
            custom_histories = [custom_gen.get_custom_history(extractor, tag)]
        elif inspect.isfunction(extractor):
            urls = extractor()
            custom_histories = [simple_history(urls, tag)]
        else:
            logger.error(f"Unexpected extractor {extractor}")
            custom_histories = []

        log_hists(custom_histories, str(extractor))
        all_histories.extend(custom_histories)

    urls_json = os.path.join(output_dir, 'urls.json')
    render(all_histories, urls_json)



main()