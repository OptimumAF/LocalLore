# LiteRT-LM host compatibility worker

M01.02 development experiment, supporting M01.03. This is a one-shot Windows
x64 CPU worker around the official Python API, not an Android integration or a
production runtime selection. The caller owns hash verification of local model
bytes, process/output bounds, cancellation, engine validation and reporting.

From the repository root, using an existing Python 3.10+ interpreter:

```powershell
python benchmarks/spike/litert/provision.py
python -m venv target/litert-spike/venv
target/litert-spike/venv/Scripts/python.exe -m pip install --no-index --no-deps target/litert-spike/litert_lm_api-0.18.1-py3-none-win_amd64.whl
target/litert-spike/venv/Scripts/python.exe -m unittest discover -s benchmarks/spike/litert -p 'test_*.py' -v
target/litert-spike/venv/Scripts/python.exe benchmarks/spike/litert/run.py --help
```

The pinned API wheel has no declared Python dependencies. The provisioner
downloads only that wheel and checks its published byte count and SHA256.
It downloads no model and changes no global Python environment. `target/` is
ignored. The coordinator supplies a separately verified `.litertlm` file:

```powershell
target/litert-spike/venv/Scripts/python.exe benchmarks/spike/litert/run.py --model <verified-local-model.litertlm>
target/litert-spike/venv/Scripts/python.exe benchmarks/spike/litert/describe.py --model <verified-local-model.litertlm>
```

Supply one UTF-8 JSON request through stdin, then close stdin. The worker accepts
at most 32 KiB, rejects duplicate/unknown keys and nonfinite numbers, and permits
only this frozen interface:

```json
{"version":1,"role":"director","prompt":"Original synthetic fixture only.","max_tokens":32,"context_tokens":4096,"threads":4,"schema":null}
```

`role` is `director` or `narrator`; `max_tokens` is an integer from 1 to 350;
`schema` is an object or null. The other settings are fixed. The prompt contains
the role's complete, coordinator-owned context and instructions. No tool is
registered and automatic tool calling is disabled. An unknown operation in a
valid JSON output still has no engine authority.

The worker uses the bundle's native prompt template, counts its rendered input
with the actual tokenizer and reserves one conservative BOS token. It refuses
input plus output reserve above 4096. The native engine is capped at 4096 and
generation at the requested output count. Thinking is disabled with a zero
thinking budget. A non-null schema requests the API's LL_GUIDANCE provider;
unsupported models/builds fail rather than silently downgrade constraints.
Completed calls report native prefill/decode counts. Initial preflight counts
are conservative rather than measured generation counts.

Stdout contains exactly one bounded JSON result using the coordinator's v1
worker contract. Only final visible text is returned. Thought channels, tools,
unknown content, exception strings and native diagnostic output are excluded.
The caller must never publish hidden channels or private inputs. Fixed errors:
`invalid_request`, `model_missing`, `model_invalid`, `runtime_unavailable`,
`model_unsupported`, `context_overflow`, `generation_failed`, `output_too_large`,
and `unsupported_output`. Success exits 0; categorized failures exit 2.

Engine, metadata and conversation use official context managers. Each invocation
loads a model afresh and closes its native resources on normal/error exits.
The outer harness terminates and waits for the worker process on timeout or
cancellation; this process containment does not establish cooperative Android
cancellation or physical-device resource behavior. No warm-cache, complete-turn,
quality, sustained-session or phone performance claim follows from a smoke run.

See [source and artifact verification](../../../docs/runtime/spike/LITERT_SOURCES.md)
and [local verification](../../../docs/runtime/spike/LITERT_VERIFICATION.md).
