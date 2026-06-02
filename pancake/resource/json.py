from json import loads, dumps
import os
import logging

logger = logging.getLogger(__name__)

def json_init():
    from pancake.settings import get_path
    json_dir = get_path("json_dir")
    data = {}
    if not os.path.exists(json_dir):
        return data
    for json in os.listdir(json_dir):
        with open(os.path.join(json_dir, json), 'r', encoding="utf-8") as f:
            data[json.split('.')[0]] = loads(f.read())

    return data
