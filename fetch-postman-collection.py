import os
import sys
import json
import http.client
from pathlib import Path

BOILERPLATE = """const getEnvelopedSchema = (schema, urlPath, requestMethod, forcedPayloadReturnType) => {
    return getSchemaGeneric(schema, urlPath, requestMethod, true, forcedPayloadReturnType);
};

const getSchema = (schema, urlPath, requestMethod, forcedPayloadReturnType) => {
    return getSchemaGeneric(schema, urlPath, requestMethod, false, forcedPayloadReturnType);
}

const getSchemaGeneric = (schema, urlPath, requestMethod, isEnvelope, forcedPayloadReturnType) => {
    const doSchema = isEnvelope ? envelopeSchema : s=>s;
    const doListSchema = isEnvelope ? listEnvelopeSchema : listSchema;
    const doDeleteSchema = isEnvelope ? deleteEnvelopeSchema : deleteSchema;

    const isListRequest = urlIsListRequest(urlPath, forcedPayloadReturnType);
    if(requestMethod === "GET" && isListRequest){
        return doListSchema(schema);
    }
    if(requestMethod === "DELETE"){
        return doDeleteSchema(schema);
    }
    return doSchema(schema);
}

const urlIsListRequest = (urlPath, forcedPayloadReturnType) => {
    if (forcedPayloadReturnType && ["list", "object"].includes(forcedPayloadReturnType)){
        return forcedPayloadReturnType;
    }
    const lastPathItem = urlPath[urlPath.length-1];
    // if the URL doesn't end with a UUID
    return !/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/.test(lastPathItem);
};

const envelopeSchema = (schema) => {
    return {
        "type": "object",
        "additionalProperties": false,
        "required": ["data", "_metadata"],
        "properties": {
            "data": schema,
            "_metadata": {
                "type": "object",
                "additionalProperties": false,
                "required": ["pagination"],
                "properties": {
                    "pagination": {
                        "type": ["object", "null"],
                        "additionalProperties": false,
                        "required": ["sortColumn", "sortOrder", "limit", "offset", "total"],
                        "properties": {
                            "sortColumn": {"type": ["string", "null"]},
                            "sortOrder": {"type": ["string", "null"]},
                            "limit": {"type": ["number", "null"]},
                            "offset": {"type": ["number", "null"]},
                            "total": {"type": ["number", "null"]}
                        }
                    }
                }
            }
        }
    }
};

const listEnvelopeSchema = (schema) => {
    return envelopeSchema(listSchema(schema));
}

const listSchema = (schema) => {
    return {
        "type": "array",
        "items": schema
    };
}

const deleteEnvelopeSchema = (schema) => {
    return {
        "type": "object",
        "additionalProperties": false,
        "required": ["data", "deleted", "originalObject"],
        "properties": {
            "deleted": {"type": "boolean"},
            "data": {"type": "null"},
            "originalObject": schema,
            "message": {"type": "string"}
        }
    }
}

const deleteSchema = (schema) => {
    return {
        "type": "object",
        "additionalProperties": false,
        "required": ["deleted", "originalObject"],
        "properties": {
            "deleted": {"type": "boolean"},
            "originalObject": schema,
            "message": {"type": "string"}
        }
    }
}

const errorsEnvelopeSchema = () => {
    return {
        "type": "object",
        "additionalProperties": false,
        "properties": {
            "errors": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties":{
                        "error": {"type": "string"},
                        "originalObject": {"type": "string"}
                    }
                }
            }
        }
    }
};

const errorsSchema = () => {
    return {
        "type": "object",
        "additionalProperties": false,
        "properties": {
            "type": "object",
            "properties":{
                "error": {"type": "string"},
                "originalObject": {"type": "string"}
            }
        }
    }
};

const bedrockTestHelpers = {
    getEnvelopedSchema,
    getSchema,
    errorsEnvelopeSchema,
    errorsSchema
};"""

BOILERPLATE = [f'"{line.replace('"', '\\"')}",' for line in BOILERPLATE.split("\n")]


def postman_request(method: str, endpoint: str, key: str, payload: dict = None, expected_status: int = 200):
    conn = http.client.HTTPSConnection("api.getpostman.com")
    payload = json.dumps(payload) if payload else ""
    headers = {"Accept": "application/vnd.api.v10+json", "X-API-Key": key}
    conn.request(method, endpoint, payload, headers)
    res = conn.getresponse()
    if res.status != expected_status:
        raise Exception(f"Request failed with status {res.status}: {res.reason}")
    data = res.read()
    return json.loads(data.decode("utf-8"))


def get_collections(collection_name: str, key: str):
    collections = postman_request("GET", "/collections", key)
    return [c for c in collections["collections"] if c["name"].lower() == collection_name.lower()]


def sort_collection(collection):
    return sorted(collection, key=lambda c: c["updatedAt"], reverse=True)


def get_collection_for_branch(collections: list[dict], branch: str):
    main_collection = sort_collection([c for c in collections if "fork" not in c])
    if not main_collection:
        print("ERROR: Unable to find main collection. Using first collection.")
        raise Exception("Unable to find main collection")
    _collections = sort_collection([c for c in collections if "fork" in c and c["fork"]["label"] == branch])
    if not _collections:
        if branch != "main":
            print(f"WARN: Unable to find collection for {branch}. Using main collection.")
        return main_collection[0]
    return _collections[0]


def export_collection(collection_id: str, path: str, key: str):
    collection_export = postman_request("GET", f"/collections/{collection_id}", key)
    dirname = os.path.dirname(path)
    Path(dirname).mkdir(parents=True, exist_ok=True)
    lines = []
    for line in json.dumps(collection_export, indent=2).split("\n"):
        if "const bedrockTestHelpers = pm.require('@keyholding/bedrock-test-helpers');" in line:
            lines.extend(BOILERPLATE)
        else:
            lines.append(line)
    with open(path, "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    COLLECTION_NAME = sys.argv[1]
    POSTMAN_KEY = sys.argv[2]
    OUTPUT_PATH = sys.argv[3]
    BRANCH = sys.argv[4]
    all_collections = get_collections(COLLECTION_NAME, POSTMAN_KEY)
    if not all_collections:
        print(f"Collection {COLLECTION_NAME} not found")
        sys.exit(1)
    collection = get_collection_for_branch(all_collections, BRANCH)
    print(collection)
    export_collection(collection["uid"], OUTPUT_PATH, POSTMAN_KEY)
    print(f"Collection {COLLECTION_NAME} exported to {OUTPUT_PATH}")
