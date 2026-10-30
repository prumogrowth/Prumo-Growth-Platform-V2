"""OPS-02: bounded offline validation of synthetic, untrusted declarations.

No execution, authentication, attestation or referenced-evidence retrieval.
The contract is compiled below; importing this module does not read files.
"""
import hashlib
import json
import os
import re
import stat
import sys
import uuid
from datetime import datetime

VERSION = "prumo.s0s1.authority.evidence.v1"
MAX_DOCUMENTS = 32
MAX_BYTES = 65536
MAX_TOTAL_BYTES = 1048576
MAX_DEPTH = 8
ACTIONS = ("APPOINT", "REVOKE", "REACTIVATE")
STATES = {
    "INTENTION_RECORDED": ("NOT_CLAIMED",),
    "PROVISIONAL_RESULT": ("UNPROVEN",),
    "COMMIT_NOT_PROVEN": ("UNPROVEN",),
    "RECONCILED_DECLARED": ("DECLARED_COMMITTED",),
    "FAILURE": ("UNPROVEN", "DECLARED_NOT_COMMITTED"),
    "CONFLICT": ("DECLARED_NOT_COMMITTED",),
}
COMMON = {"version", "kind", "data_classification", "authorizes_action",
          "act_id", "action", "target_id", "environment", "cas", "digest"}
INTENTION_FIELDS = COMMON | {"operator_ref", "authorization_ref", "evidence"}
RECEIPT_FIELDS = COMMON | {"intention_digest", "attempt_id", "state",
                          "commit_claim", "posterior_evidence"}
HEX = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
REF = re.compile(r"synthetic:[a-z0-9][a-z0-9_-]{0,63}\Z", re.ASCII)
COMPONENT = re.compile(r"[A-Za-z0-9_-][A-Za-z0-9_.-]{0,127}\Z", re.ASCII)


class Invalid(ValueError):
    def __init__(self, code, location="document"):
        self.code = code
        self.location = location
        self.args = (code,)


def need(condition, code, location="document"):
    if not condition:
        raise Invalid(code, location)


def fields(value, required, optional=frozenset(), location="document"):
    need(type(value) is dict, "OBJECT_REQUIRED", location)
    need(not (set(value) - required - optional), "UNKNOWN_FIELD", location)
    need(not (required - set(value)), "MISSING_FIELD", location)


def digest_string(value, location):
    need(type(value) is str and HEX.fullmatch(value) is not None,
         "INVALID_SHA256", location)


def reference(value, location):
    need(type(value) is str and REF.fullmatch(value) is not None,
         "INVALID_SYNTHETIC_REFERENCE", location)


def identifier(value, location):
    need(type(value) is str, "INVALID_UUID", location)
    try:
        parsed = uuid.UUID(value)
    except ValueError:
        raise Invalid("INVALID_UUID", location) from None
    need(str(parsed) == value and parsed.int != 0
         and parsed.variant == uuid.RFC_4122, "INVALID_UUID", location)


def canonical_bytes(document):
    """Only the top-level digest is excluded; no mutation or normalization."""
    payload = {key: value for key, value in document.items() if key != "digest"}
    return json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


def document_digest(document):
    domain = (VERSION + "\0" + document["kind"] + "\0").encode("ascii")
    return hashlib.sha256(domain + canonical_bytes(document)).hexdigest()


def evidence(value, location):
    fields(value, {"ref", "sha256"}, location=location)
    reference(value["ref"], location + ".ref")
    digest_string(value["sha256"], location + ".sha256")


def validate_document(document):
    need(type(document) is dict, "OBJECT_REQUIRED")
    need(document.get("version") == VERSION, "UNSUPPORTED_VERSION")
    kind = document.get("kind")
    need(type(kind) is str and kind in ("INTENTION", "RECEIPT"), "UNKNOWN_KIND")
    fields(document, INTENTION_FIELDS if kind == "INTENTION" else RECEIPT_FIELDS,
           {"declared_at"})
    need(document["data_classification"] == "SYNTHETIC", "SYNTHETIC_ONLY")
    need(document["authorizes_action"] is False, "AUTHORIZATION_CLAIM_FORBIDDEN")
    identifier(document["act_id"], "act_id")
    identifier(document["target_id"], "target_id")
    need(type(document["action"]) is str and document["action"] in ACTIONS,
         "UNKNOWN_ACTION", "action")
    fields(document["environment"], {"kind", "id"}, location="environment")
    need(document["environment"]["kind"] == "SYNTHETIC_OFFLINE",
         "SYNTHETIC_ONLY", "environment.kind")
    reference(document["environment"]["id"], "environment.id")
    fields(document["cas"], {"scheme", "observed_sha256"}, location="cas")
    need(document["cas"]["scheme"] == "i86.snapshot.sha256", "UNKNOWN_CAS", "cas")
    digest_string(document["cas"]["observed_sha256"], "cas.observed_sha256")
    if "declared_at" in document:
        value = document["declared_at"]
        need(type(value) is str and re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", value),
            "INVALID_DECLARED_TIME", "declared_at")
        try:
            datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            raise Invalid("INVALID_DECLARED_TIME", "declared_at") from None
    if kind == "INTENTION":
        reference(document["operator_ref"], "operator_ref")
        reference(document["authorization_ref"], "authorization_ref")
        evidence(document["evidence"], "evidence")
    else:
        identifier(document["attempt_id"], "attempt_id")
        digest_string(document["intention_digest"], "intention_digest")
        state, claim = document["state"], document["commit_claim"]
        need(type(state) is str and state in STATES, "UNKNOWN_RECEIPT_STATE", "state")
        need(type(claim) is str and claim in STATES[state],
             "CONTRADICTORY_RECEIPT", "commit_claim")
        evidence(document["posterior_evidence"], "posterior_evidence")
    digest_string(document["digest"], "digest")
    need(document["digest"] == document_digest(document), "DIGEST_MISMATCH", "digest")


def pairs(items):
    result = {}
    for key, value in items:
        need(key not in result, "DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def reject_constant(_value):
    raise Invalid("NONFINITE_JSON_NUMBER")


def bounded_value(value, depth=0):
    need(depth <= MAX_DEPTH, "MAX_DEPTH_EXCEEDED")
    if type(value) is dict:
        for child in value.values():
            bounded_value(child, depth + 1)
    elif type(value) is list:
        raise Invalid("ARRAY_NOT_SUPPORTED")
    else:
        need(type(value) in (str, bool), "UNSUPPORTED_JSON_VALUE")


def decode_document(raw):
    need(type(raw) is bytes and len(raw) <= MAX_BYTES, "DOCUMENT_SIZE_LIMIT")
    try:
        document = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                              parse_constant=reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        if isinstance(exc, Invalid):
            raise
        raise Invalid("MALFORMED_JSON") from None
    bounded_value(document)
    validate_document(document)
    return document


def result(errors, count):
    return {
        "version": VERSION,
        "status": "INVALID_UNTRUSTED" if errors else "FORMALLY_VALID_UNTRUSTED",
        "authorizes_action": False,
        "human_identity_verified": False,
        "organizational_authorization_verified": False,
        "origin_authenticated": False,
        "referenced_evidence_bytes_verified": False,
        "commit_proven": False,
        "documents_checked": count,
        "errors": errors,
    }


def validate_bytes(documents):
    """One bounded bundle; duplicate detection is limited to this invocation."""
    parsed = []
    try:
        need(type(documents) in (list, tuple) and 0 < len(documents) <= MAX_DOCUMENTS,
             "DOCUMENT_COUNT_LIMIT")
        need(all(type(raw) is bytes for raw in documents), "BYTES_REQUIRED")
        need(sum(len(raw) for raw in documents) <= MAX_TOTAL_BYTES, "TOTAL_SIZE_LIMIT")
        for raw in documents:
            parsed.append(decode_document(raw))
        intentions, attempts = {}, {}
        for item in parsed:
            if item["kind"] == "INTENTION":
                previous = intentions.get(item["act_id"])
                need(previous is None or previous["digest"] == item["digest"],
                     "ACT_ID_CONTENT_CONFLICT")
                intentions[item["act_id"]] = item
        need(bool(intentions), "INTENTION_REQUIRED")
        for item in parsed:
            if item["kind"] != "RECEIPT":
                continue
            intention = intentions.get(item["act_id"])
            need(intention is not None, "INTENTION_NOT_FOUND")
            for key in ("action", "target_id", "environment", "cas"):
                need(item[key] == intention[key], "BINDING_MISMATCH", key)
            need(item["intention_digest"] == intention["digest"],
                 "INTENTION_DIGEST_MISMATCH")
            previous = attempts.get(item["attempt_id"])
            need(previous is None or previous == item["digest"], "ATTEMPT_CONTENT_CONFLICT")
            attempts[item["attempt_id"]] = item["digest"]
    except Invalid as exc:
        return result([{"code": exc.code, "location": exc.location}], len(parsed))
    return result([], len(parsed))


def safe_documents(root, names):
    """POSIX no-follow descriptor traversal; bounded reads of explicit JSON files.

    No path resolution through symlinks, no FIFO/device/socket opening for data,
    no traversal, absolute document path, implicit evidence lookup or glob.
    """
    need(type(root) is str and root.startswith("/") and len(root) <= 4096,
         "UNSAFE_ROOT")
    root_parts = root.split("/")[1:]
    need(root != "/" and all(part and COMPONENT.fullmatch(part) for part in root_parts),
         "UNSAFE_ROOT")
    need(0 < len(names) <= MAX_DOCUMENTS, "DOCUMENT_COUNT_LIMIT")
    for name in names:
        need(type(name) is str and len(name) <= 256, "UNSAFE_PATH")
        parts = name.split("/")
        need(0 < len(parts) <= 8 and name.endswith(".json")
             and all(part not in (".", "..") and COMPONENT.fullmatch(part) for part in parts),
             "UNSAFE_PATH")
    descriptors = []
    try:
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
        root_fd = os.open("/", flags)
        descriptors.append(root_fd)
        for part in root_parts:
            root_fd = os.open(part, flags, dir_fd=root_fd)
            descriptors.append(root_fd)
        documents, total = [], 0
        for name in names:
            parent_fd, local = root_fd, []
            try:
                for part in name.split("/")[:-1]:
                    parent_fd = os.open(part, flags, dir_fd=parent_fd)
                    local.append(parent_fd)
                fd = os.open(name.split("/")[-1], os.O_RDONLY | os.O_NOFOLLOW
                             | os.O_CLOEXEC | os.O_NONBLOCK, dir_fd=parent_fd)
                local.append(fd)
                before = os.fstat(fd)
                need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1,
                     "UNSAFE_FILE_TYPE")
                need(before.st_size <= MAX_BYTES, "DOCUMENT_SIZE_LIMIT")
                chunks, size = [], 0
                while True:
                    chunk = os.read(fd, min(8192, MAX_BYTES + 1 - size))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    size += len(chunk)
                    need(size <= MAX_BYTES, "DOCUMENT_SIZE_LIMIT")
                after = os.fstat(fd)
                need((before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
                     (after.st_size, after.st_mtime_ns, after.st_ctime_ns),
                     "INPUT_CHANGED_DURING_READ")
                total += size
                need(total <= MAX_TOTAL_BYTES, "TOTAL_SIZE_LIMIT")
                documents.append(b"".join(chunks))
            finally:
                for fd in reversed(local):
                    os.close(fd)
        return documents
    except OSError:
        raise Invalid("UNSAFE_OR_UNREADABLE_PATH") from None
    finally:
        for fd in reversed(descriptors):
            os.close(fd)


def main(argv=None):
    # Small strict grammar, so even usage errors have the same JSON envelope.
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        need(len(args) >= 3 and args[0] == "--input-root", "USAGE",
             "--input-root ABSOLUTE_DIRECTORY RELATIVE.json [RELATIVE.json ...]")
        documents = safe_documents(args[1], args[2:])
        report = validate_bytes(documents)
    except Invalid as exc:
        report = result([{"code": exc.code, "location": exc.location}], 0)
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0 if report["status"] == "FORMALLY_VALID_UNTRUSTED" else 2


if __name__ == "__main__":
    sys.exit(main())
