import os
import sys
import json
import http.client
from pathlib import Path


def postman_request(method: str, endpoint: str, key: str, payload: dict = None, expected_status: int = 200):
    conn = http.client.HTTPSConnection("api.getpostman.com")
    payload = json.dumps(payload) if payload else ""
    headers = {
        'Accept': 'application/vnd.api.v10+json',
        'X-API-Key': key
    }
    conn.request(method, endpoint, payload, headers)
    res = conn.getresponse()
    if res.status != expected_status:
        raise Exception(f"Request failed with status {res.status}: {res.reason}")
    data = res.read()
    return json.loads(data.decode("utf-8"))


def get_collections(collection_name: str, key: str):
    collections = postman_request("GET", "/collections", key)
    return [c for c in collections['collections'] if c['name'].lower() == collection_name]


def get_collection_for_branch(collections: list[dict], branch: str):
    main_collection = [c for c in collections if 'fork' not in c]
    if not main_collection:
        print("ERROR: Unable to find main collection. Using first collection.")
        raise Exception("Unable to find main collection")
    _collections = [c for c in collections if 'fork' in c and c['fork']['label'] == branch]
    if not _collections:
        print(f"WARN: Unable to find collection for {branch}. Using main collection.")
        return main_collection[0]
    return _collections[0]


def export_collection(collection_id: str, path: str, key: str):
    collection_export = postman_request("GET", f"/collections/{collection_id}", key)
    dirname = os.path.dirname(path)
    Path(dirname).mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        f.write(json.dumps(collection_export, indent=2))


if __name__ == '__main__':
    COLLECTION_NAME = sys.argv[1]
    POSTMAN_KEY = sys.argv[2]
    OUTPUT_PATH = sys.argv[3]
    BRANCH = sys.argv[4]
    all_collections = get_collections(COLLECTION_NAME, POSTMAN_KEY)
    if not all_collections:
        print(f"Collection {COLLECTION_NAME} not found")
        sys.exit(1)
    collection = get_collection_for_branch(all_collections, BRANCH)
    export_collection(collection['uid'], OUTPUT_PATH, POSTMAN_KEY)
    print(f"Collection {COLLECTION_NAME} exported to {OUTPUT_PATH}")
