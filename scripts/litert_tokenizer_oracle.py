"""Opt-in private selected-tokenizer extraction; never imports an inference engine.

Weights are authenticated on a held source handle, never copied to output.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys

ROOT = Path(__file__).resolve().parents[1]
SCOPE = "locallore_litert_selected_tokenizer_v1"
BARRIER = b"locallore_selected_tokenizer_owned_v1\n"
MODEL_BYTES = 2_588_147_712
MODEL_SHA256 = "181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c"
SOURCE_FILES = ("scripts/litert_tokenizer_oracle.py", "benchmarks/litert_tokenizer_metadata.py",
                "benchmarks/litert_tokenizer_oracle.py", "benchmarks/model_integrity.py")


class SelectedTokenizerRefused(Exception):
    pass


def require(value, reason):
    if not value:
        raise SelectedTokenizerRefused(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pairs(rows):
    result = {}
    for key, value in rows:
        require(key not in result, "invalid_json")
        result[key] = value
    return result


def read_json(path):
    no_links(path)
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and 0 < info.st_size <= 65536, "invalid_json")
    with path.open("rb") as source:
        raw = source.read(65537)
    require(len(raw) <= 65536, "invalid_json")
    try:
        return json.loads(raw, object_pairs_hook=pairs,
                          parse_constant=lambda _: require(False, "invalid_json"))
    except (ValueError, UnicodeError):
        raise SelectedTokenizerRefused("invalid_json") from None


def no_links(path):
    require(path.is_absolute(), "unsafe_path")
    for part in (path, *path.parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(info.st_mode) and not getattr(info, "st_file_attributes", 0) & 0x400,
                "unsafe_path")


def private_output(value):
    path = Path(value)
    no_links(path)
    require(path == path.resolve() and not path.exists() and path.parent.is_dir(), "output_exists_or_unsafe")
    require(not any((part / ".git").exists() for part in (path, *path.parents)), "private_output_required")
    return path


def private_entry(path):
    no_links(path)
    require(path.is_absolute() and path == path.resolve() and path.parent.is_dir(), "unsafe_path")
    require(not any((part / ".git").exists() for part in (path, *path.parents)), "private_output_required")
    return path


def module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def create(path, raw):
    private_entry(path)
    with path.open("xb") as output:
        output.write(raw); output.flush(); os.fsync(output.fileno())


def validate(proposal_path, authorization_path):
    for path in (proposal_path, authorization_path):
        no_links(path)
    value = read_json(proposal_path)
    auth = read_json(authorization_path)
    require(type(value) is dict and set(value) == {"version", "scope", "source", "source_commit", "source_files",
            "output", "allow_source_reads", "root_go_pending"}, "proposal_invalid")
    require(type(value["version"]) is int and value["version"] == 1 and value["scope"] == SCOPE
            and value["allow_source_reads"] is False and value["root_go_pending"] is True, "proposal_invalid")
    require(type(value["source_commit"]) is str and re.fullmatch(r"[a-f0-9]{40}", value["source_commit"]), "proposal_invalid")
    require(type(value["source_files"]) is dict and set(value["source_files"]) == set(SOURCE_FILES), "source_changed")
    for name, digest in value["source_files"].items():
        require(type(digest) is str and re.fullmatch(r"[a-f0-9]{64}", digest)
                and sha((ROOT / name).read_bytes()) == digest, "source_changed")
    identity = value["source"]
    require(type(identity) is dict and set(identity) == {"path", "bytes", "sha256"}
            and type(identity["path"]) is str and type(identity["bytes"]) is int
            and identity["bytes"] == MODEL_BYTES and identity["sha256"] == MODEL_SHA256, "source_identity")
    source = Path(identity["path"])
    no_links(source)
    require(source == source.resolve(), "unsafe_path")
    require(auth == {"version": 1, "proposal_sha256": sha(proposal_path.read_bytes()),
            "allow_full_source_hash": True, "allow_selected_metadata_read": True,
            "allow_native": False, "root_go_pending": False} and type(auth["version"]) is int,
            "not_authorized")
    require(auth["allow_full_source_hash"] is True and auth["allow_selected_metadata_read"] is True
            and auth["allow_native"] is False and auth["root_go_pending"] is False, "not_authorized")
    require(type(value["output"]) is str, "proposal_invalid")
    output = private_output(value["output"])
    return source, output, value


def full_hash(source, size):
    source.seek(0)
    digest = hashlib.sha256(); total = 0
    while total < size:
        block = source.read(min(1024 * 1024, size - total))
        require(bool(block), "source_changed")
        digest.update(block); total += len(block)
    require(source.read(1) == b"", "source_changed")
    return digest.hexdigest()


def validate_report(value, proposal, output):
    private_entry(output / "selection.json")
    keys = {"version", "scope", "status", "source_commit", "source_bytes", "source_sha256",
            "source_verified_twice", "container_version", "header_end", "section_count", "kind", "selection",
            "artifacts", "tokenizer_range", "metadata_range", "weight_payloads_published", "native_loaded"}
    require(type(value) is dict and set(value) == keys, "worker_report_invalid")
    require(type(value["version"]) is int and value["version"] == 1 and value["scope"] == SCOPE
            and value["status"] == "extracted" and value["source_commit"] == proposal["source_commit"]
            and type(value["source_bytes"]) is int and value["source_bytes"] == MODEL_BYTES
            and value["source_sha256"] == MODEL_SHA256 and value["source_verified_twice"] is True
            and value["weight_payloads_published"] is False and value["native_loaded"] is False, "worker_report_invalid")
    version = value["container_version"]
    require(type(version) is list and len(version) == 3 and all(type(x) is int and 0 <= x < 2 ** 32 for x in version)
            and version[0] == 1 and version[1] <= 7, "worker_report_invalid")
    require(type(value["header_end"]) is int and 36 <= value["header_end"] <= 4 * 1024 * 1024
            and type(value["section_count"]) is int and 1 <= value["section_count"] <= 256
            and value["kind"] in ("HF_JSON", "SENTENCEPIECE") and value["selection"] in ("TYPED", "UNTYPED"),
            "worker_report_invalid")
    for key in ("tokenizer_range", "metadata_range"):
        interval = value[key]
        require(type(interval) is list and len(interval) == 2 and all(type(x) is int for x in interval)
                and value["header_end"] <= interval[0] < interval[1] <= MODEL_BYTES
                and interval[0] % (16 * 1024) == 0, "worker_report_invalid")
    require(max(value["tokenizer_range"][0], value["metadata_range"][0]) >=
            min(value["tokenizer_range"][1], value["metadata_range"][1]), "worker_report_invalid")
    artifacts = value["artifacts"]
    names = {"selected-tokenizer.bin", "llm-metadata.pb"} | ({"tokenizer.json"} if value["kind"] == "HF_JSON" else set())
    require(type(artifacts) is dict and set(artifacts) == names, "worker_report_invalid")
    require({p.name for p in output.iterdir()} == names | {"selection.json"}, "worker_report_invalid")
    for name, item in artifacts.items():
        cap = (128 if name == "tokenizer.json" else 32 if name == "selected-tokenizer.bin" else 1) * 1024 * 1024
        require(type(item) is dict and set(item) == {"bytes", "sha256"}
                and type(item["bytes"]) is int and 0 < item["bytes"] <= cap
                and type(item["sha256"]) is str and re.fullmatch(r"[a-f0-9]{64}", item["sha256"]), "worker_report_invalid")
        path = private_entry(output / name)
        require(path.is_file() and path.stat().st_size == item["bytes"], "worker_report_invalid")
        with path.open("rb") as source:
            require(full_hash(source, item["bytes"]) == item["sha256"], "worker_report_invalid")
    require(artifacts["selected-tokenizer.bin"]["bytes"] == value["tokenizer_range"][1] - value["tokenizer_range"][0]
            and artifacts["llm-metadata.pb"]["bytes"] == value["metadata_range"][1] - value["metadata_range"][0],
            "worker_report_invalid")
    return True


def extract(proposal_path, authorization_path):
    source_path, output, value = validate(proposal_path, authorization_path)
    reader = module("selected_metadata_reader", "benchmarks/litert_tokenizer_metadata.py")
    integrity = module("selected_metadata_integrity", "benchmarks/model_integrity.py")
    initial = source_path.lstat()
    require(stat.S_ISREG(initial.st_mode) and initial.st_size == MODEL_BYTES, "source_identity")
    with source_path.open("rb") as source:
        opened = os.fstat(source.fileno())
        require(integrity.fingerprint(initial) == integrity.fingerprint(opened), "source_changed")
        require(full_hash(source, MODEL_BYTES) == MODEL_SHA256, "source_identity")
        try:
            selected = reader.extract_tokenizer_metadata(source, MODEL_BYTES)
        except reader.TokenizerMetadataRefused as failure:
            raise SelectedTokenizerRefused("metadata_" + failure.reason.value) from None
        require(full_hash(source, MODEL_BYTES) == MODEL_SHA256, "source_changed")
        require(integrity.fingerprint(opened) == integrity.fingerprint(os.fstat(source.fileno())), "source_changed")
    require(integrity.fingerprint(initial) == integrity.fingerprint(source_path.lstat()), "source_changed")
    require(bool(selected.llm_metadata), "metadata_empty_eos")
    private_output(str(output))
    output.mkdir()
    artifacts = {"selected-tokenizer.bin": selected.original_payload, "llm-metadata.pb": selected.llm_metadata}
    if selected.decoded_json is not None:
        artifacts["tokenizer.json"] = selected.decoded_json
    entries = {}
    for name, data in artifacts.items():
        create(output / name, data)
        private_entry(output / name)
        require(sha((output / name).read_bytes()) == sha(data), "publication_failed")
        entries[name] = {"bytes": len(data), "sha256": sha(data)}
    report = {"version": 1, "scope": SCOPE, "status": "extracted", "source_commit": value["source_commit"],
              "source_bytes": MODEL_BYTES, "source_sha256": MODEL_SHA256, "source_verified_twice": True,
              "container_version": list(selected.container_version), "header_end": selected.header_end,
              "section_count": len(selected.sections), "kind": selected.selected_kind.value,
              "selection": selected.selection.value, "artifacts": entries,
              "tokenizer_range": [selected.tokenizer_range.begin, selected.tokenizer_range.end],
              "metadata_range": [selected.metadata_range.begin, selected.metadata_range.end],
              "weight_payloads_published": False, "native_loaded": False}
    create(output / "selection.json", encoded(report))
    return report


class Arguments(argparse.ArgumentParser):
    def error(self, message):
        raise SelectedTokenizerRefused("arguments")


def main(argv=None):
    try:
        parser = Arguments(allow_abbrev=False)
        parser.add_argument("mode", choices=("extract", "_extract-worker"))
        parser.add_argument("--proposal", type=Path, required=True)
        parser.add_argument("--authorization", type=Path, required=True)
        args = parser.parse_args(argv)
        if args.mode == "_extract-worker":
            require(sys.stdin.buffer.read(4097) == BARRIER, "owner_barrier")
            result = extract(args.proposal, args.authorization)
        else:
            source, output, proposal = validate(args.proposal, args.authorization)
            evidence = private_output(str(output.with_name(output.name + "-owner")))
            evidence.mkdir()
            create(evidence / "start.json", encoded({"version": 1,
                "proposal_sha256": sha(args.proposal.read_bytes()),
                "authorization_sha256": sha(args.authorization.read_bytes())}))
            sys.path.insert(0, str(ROOT / "benchmarks"))
            from runtime_spike import run_process
            result = run_process([sys.executable, "-I", "-S", "-B", str(Path(__file__).resolve()), "_extract-worker",
                "--proposal", str(args.proposal), "--authorization", str(args.authorization)],
                request=BARRIER, deadline=180, max_output=262144)
            create(evidence / "worker-stdout.bin", result.stdout)
            create(evidence / "owned-result.json", encoded({key: item for key, item in vars(result).items() if key != "stdout"}))
            require(result.status == "completed" and result.returncode == 0 and result.cleanup_complete,
                    "worker_failed")
            observed = json.loads(result.stdout, object_pairs_hook=pairs)
            require(observed == read_json(output / "selection.json") and observed["scope"] == SCOPE
                    and observed["status"] == "extracted", "worker_report_invalid")
            validate_report(observed, proposal, output)
            result = observed
        print(encoded(result).decode("ascii").strip())
        return 0
    except SelectedTokenizerRefused as failure:
        reason = str(failure)
    except Exception:
        reason = "local_tool_failure"
    print(json.dumps({"version": 1, "scope": SCOPE, "status": "failed", "reason": reason}))
    return 2


if __name__ == "__main__": raise SystemExit(main())
