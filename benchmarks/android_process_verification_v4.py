"""Closed byte-bound owned-target replay; no process, socket or credential API.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
from pathlib import Path, PureWindowsPath

from benchmarks import owned_target_contract as c
from benchmarks import isolated_adb_lease as base
from benchmarks import receipt_avd_environment as env
from benchmarks import host_commit_capacity as commit


# Shared mechanism only; public legacy entrypoints below always select v1.
class _Verifier:

    def __init__(self, contract):
        self.c = contract

    def _raw(self, pin, cap=2 * 1024 * 1024):
        self.c.binding(pin, max_bytes=cap)
        return base._read_bound(pin, cap=cap)

    def _json(self, pin):
        return env.decode_json(self._raw(pin))

    def _at(self, pin, path):
        self.c.binding(pin)
        self.c._need(PureWindowsPath(pin['path']) == PureWindowsPath(path), 'binding')
        return self._json(pin)

    def _pin(self, path):
        self.c._path(str(path), project=True)
        return env.binding(path)

    def _equal(self, a, b, reason='binding'):
        self.c._need(self.c._same(a, b), reason)

    def verify_proof(self, pin, session, context):
        root = PureWindowsPath(session['root']) / 'proofs'
        expected = root / ('command-%04d-%s.json' % (context['index'], context['phase']))
        proof = self.c.validate_proof(self._at(pin, expected), session, context)
        session_pin = self._pin(Path(session['root']) / self.c.SESSION_FILE)
        self._equal(proof['session'], session_pin)
        q = self.c.validate_query_bundle(self._json(proof['queries']), session['descriptor'], session['caller'], session['admission'], session['running'])
        self.c._need(q == session['descriptor']['transport_id'], 'identity')
        queries = self._json(proof['queries'])['queries']
        self._equal([proof['version_response_hex'], proof['devices_response_hex']], [x['response_hex'] for x in queries])
        return proof

    def verify_client_record(self, binding, session, admission):
        a = self.c.validate_admission(admission)
        s = self.c.validate_session(session, a)
        session_pin = self._pin(Path(s['root']) / self.c.SESSION_FILE)
        self._equal(self._json(session_pin), s)
        self._equal(self.c.validate_admission(self._json(s['admission'])), a)
        self._equal(self.c.validate_running(self._json(s['running']), a, s['admission']), s['descriptor'])
        value = self.c.validate_client_record(self._json(binding), s)
        expected = PureWindowsPath(s['root']) / 'clients' / ('command-%04d.json' % value['index'])
        self.c._need(PureWindowsPath(binding['path']) == expected, 'binding')
        self._equal(value['session'], session_pin)
        self.c.validate_operation(value['operation'], a)
        total = 0
        for channel in ('stdout', 'stderr'):
            raw_path = expected.with_suffix('.' + channel + '.bin')
            self.c._need(PureWindowsPath(value[channel]['path']) == raw_path, 'binding')
            raw = self._raw(value[channel], cap=16 * 1024 * 1024)
            total += len(raw)
        self.c._need(total <= 16 * 1024 * 1024, 'binding')
        self.c._need(value['client_qualified'] is True, 'capability')
        proofs = []
        for phase, key in (('before', 'server_before'), ('after', 'server_after')):
            context = dict(index=value['index'], phase=phase, label=value['label'], operation_sha256=value['operation_sha256'], transport_id=value['transport_id'])
            proofs.append(self.verify_proof(value[key], s, context))
        for key in ('anchor', 'endpoint', 'caller'):
            self._equal(proofs[0][key], proofs[1][key])
        if value['operation']['stdin'] is not None:
            env.check_binding(value['operation']['stdin'])
        if value['operation']['argv'][:2] == ['am', 'instrument']:
            method = value['operation']['argv'][6]
            kind = self.c.instrumentation_kind(value['operation']['argv'])
            path = Path(a['root']) / 'claims-v1' / (kind + '-v1.json')
            self.c.validate_claim(self._json(self._pin(path)), s['admission'], s['caller'], kind, value['operation_sha256'])
        return copy.deepcopy(value)

    def require_current_clients(self, root, count, session_binding, admission):
        self.c._int(count, 1, 10000)
        root = Path(root)
        s = self.c.validate_session(self._json(session_binding), admission)
        self.c._need(PureWindowsPath(s['root']) == PureWindowsPath(str(root)), 'binding')
        self._equal(session_binding, self._pin(root / self.c.SESSION_FILE))
        expected_clients = set()
        expected_proofs = set()
        rows = []
        for index in range(1, count + 1):
            stem = 'command-%04d' % index
            expected_clients |= {stem + '.json', stem + '.stdout.bin', stem + '.stderr.bin'}
            for phase in ('before', 'after'):
                expected_proofs |= {stem + '-' + phase + '.json', stem + '-' + phase + '-queries-v1.json'}
            rows.append(self.verify_client_record(self._pin(root / 'clients' / (stem + '.json')), s, admission))
            self.c._need(rows[-1]['index'] == index, 'binding')
        for folder, names in (('clients', expected_clients), ('proofs', expected_proofs)):
            directory = env.safe_path(root / folder, directory=True)
            self.c._need({p.name for p in directory.iterdir()} == names, 'binding')
            for path in directory.iterdir():
                env.safe_path(path)
        return rows

    def _capture(self, pin, path, process, returncode):
        self.c._need(path.name in ('server-output-v1', 'guest-output-v1'), 'binding')
        value = self._at(pin, path.parent / (path.name.replace('-output-', '-capture-') + '.json'))
        self.c._obj(value, ('version', 'protocol', 'server', 'status', 'returncode', 'stdout', 'stderr', 'stdout_bytes', 'stderr_bytes', 'capture_complete', 'pipes_closed'))
        self.c._int(value['version'], 1, 1)
        self.c._need(value['protocol'] == self.c.PROTOCOL)
        self._equal(value['server'], process)
        self.c._need(value['status'] in ('terminated', 'exited') and type(value['returncode']) is int and (value['returncode'] == returncode) and (value['capture_complete'] is True) and (value['pipes_closed'] is True), 'identity')
        for channel in ('stdout', 'stderr'):
            self.c._int(value[channel + '_bytes'], 0, 262144, 'binding')
            self.c._need(PureWindowsPath(value[channel]['path']) == PureWindowsPath(str(path)) / ('owner-' + channel + '-v1.bin'), 'binding')
            self.c._need(len(self._raw(value[channel])) == value[channel + '_bytes'], 'binding')
        self.c._need(value['stdout_bytes'] + value['stderr_bytes'] <= 262144, 'binding')
        return value

    def _preflight(self, pin, path, guest=False):
        v = self._at(pin, path)
        self.c._obj(v, ('observation', 'tables', 'created_mask', 'close_attempted_mask', 'closed_mask', 'exclusive_bind_succeeded'))
        if guest:
            self.c._need(not self.c._rows(v['observation'], 'ports', [5592, 5593]), 'observation')
        else:
            base.validate_observation(v['observation'], None, None, None, require_empty=True)
        base._tables(v['tables'], v['observation'])
        for key in ('created_mask', 'close_attempted_mask', 'closed_mask'):
            self.c._int(v[key], 15 if guest else 1, 15 if guest else 1)
        self.c._need(v['exclusive_bind_succeeded'] is True, 'observation')
        return v

    def verify_guest_inputs(self, pin, admission, admission_binding):
        a = self.c.validate_admission(admission)
        g = a['guest']
        root = Path(a['root'])
        value = self._at(pin, root / 'guest-inputs-v1.json')
        self.c._obj(value, ('version', 'protocol', 'admission', 'proposal', 'authorization', 'prepared', 'prepare_result', 'token', 'original_avd', 'configuration', 'tools', 'facts', 'timer'))
        self.c._int(value['version'], 1, 1)
        self.c._need(value['protocol'] == self.c.PROTOCOL)
        for key, wanted in (('admission', admission_binding), ('proposal', g['proposal']), ('authorization', g['authorization'])):
            self._equal(value[key], wanted)
        proposal = self._json(g['proposal'])
        authorization = self._json(g['authorization'])
        env.check_authorization(authorization, 'run', g['proposal']['sha256'])
        self._equal(proposal['host_free_min'], env.root_free_min(g['root']))
        self.c._int(proposal['host_available_memory_min'], 12 * 1024 ** 3, 12 * 1024 ** 3, 'budget')
        self.c._need(proposal['version'] == 1 and proposal['phase'] == 'run' and (proposal['paths']['root'] == g['root']) and (proposal['serial'] == g['serial']) and (type(proposal['memory_mib']) is int) and (proposal['memory_mib'] == 8192) and (type(proposal['cores']) is int) and (proposal['cores'] == 4) and (proposal['max_seconds'] == 1800) and (proposal['console_port'] == 5592) and (proposal['adb_path'] == a['server']['adb']['path']), 'binding')
        for key in ('prepared', 'prepare_result'):
            self._equal(value[key], proposal[key])
        prepared = self._json(value['prepared'])
        result = self._json(value['prepare_result'])
        env.check_binding(proposal['prepare_proposal'])
        self.c._need(prepared['proposal_sha256'] == proposal['prepare_proposal']['sha256'] and prepared['avd_name'] == 'locallore_receipt_api35_v1' and (prepared['guest_boot_verified'] is False) and (prepared['userdata_absent'] is True), 'binding')
        self._equal(result, dict(version=1, proposal_sha256=proposal['prepare_proposal']['sha256'], status='completed', closure_verified=True, child_cleanup_complete=True, prepared_created=True))
        for key, pkey in (('token', 'token'), ('original_avd', 'old_avd'), ('tools', 'bindings')):
            self._equal(value[key], proposal[pkey])
        self._equal(value['configuration'], prepared['immutable'])
        for conf in value['configuration']:
            env.check_binding(conf)
        timer = value['timer']
        self.c._obj(timer, ('key', 'actual', 'effective', 'default_used', 'enabled'))
        self.c._need(timer['key'] == 'test.quitAfterBootTimeOut' and timer['enabled'] is False and (type(timer['effective']) is int) and (timer['effective'] in (-1, 0)) and (type(timer['default_used']) is bool), 'binding')
        self.c._need(timer['actual'] is None and timer['default_used'] is True and (timer['effective'] == -1) or (timer['actual'] in ('-1', '0') and timer['default_used'] is False and (timer['effective'] == int(timer['actual']))), 'binding')
        config = next((p for p in value['configuration'] if PureWindowsPath(p['path']).name == 'config.ini'))
        config_values = env.ini(self._raw(config))
        self.c._need(config_values.get(timer['key']) == timer['actual'], 'binding')
        facts = value['facts']
        self.c._obj(facts, ('free_bytes', 'available_memory', 'logical_cpus', 'commit_capacity'))
        self.c._int(facts['available_memory'], 12 * 1024 ** 3, 2 ** 63 - 1)
        self.c._int(facts['logical_cpus'], 8, 2 ** 31 - 1)
        self.c._obj(facts['free_bytes'], proposal['host_free_min'].keys())
        for drive, floor in proposal['host_free_min'].items():
            self.c._int(facts['free_bytes'][drive], floor, 2 ** 63 - 1)
        capacity = facts['commit_capacity']
        self.c._obj(capacity, ('version', 'commit_total_bytes', 'commit_limit_bytes', 'available_commit_bytes', 'guest_memory_bytes', 'required_commit_bytes', 'reserve_bytes'))
        snapshot = {k: capacity[k] for k in ('version', 'commit_total_bytes', 'commit_limit_bytes', 'available_commit_bytes')}
        try:
            expected_capacity = commit.require_capacity(snapshot, 8192)
        except commit.HostCommitRefused:
            raise self.c.TargetRefused('budget') from None
        self._equal(capacity, expected_capacity)
        return value

    def verify_owned_target_result(self, binding, admission, admission_binding, request_binding, expected_worker):
        a = self.c.validate_admission(admission)
        root = Path(a['root'])
        value = self._at(binding, root / 'worker-result-v1.json')
        self.c._obj(value, self.c.WORKER_KEYS)
        self.c._int(value['version'], 1, 1)
        self.c._need(value['protocol'] == self.c.PROTOCOL)
        for key, wanted in (('admission', admission_binding), ('request', request_binding), ('worker', expected_worker)):
            self._equal(value[key], wanted)
        req = self._at(request_binding, root / 'request-v1.json')
        self.c._obj(req, self.c.REQUEST_KEYS)
        self.c._int(req['version'], 1, 1)
        self.c._need(req['protocol'] == self.c.PROTOCOL)
        self._equal(req['admission'], admission_binding)
        self._equal(req['validated_admission'], a)
        self._equal(req['sources'], a['sources'])
        self._equal(req['python'], a['python'])
        self.c._process(req['owner'])
        self.c._int(req['owner_seconds'], a['seconds'] + 30, a['seconds'] + 30)
        script = next((p for p in a['sources'] if PureWindowsPath(p['path']).name == self.c.OWNER_SCRIPT))
        self._equal(req['worker_script'], script)
        self.c._need(value['reason'] in ('stop_requested', 'expired') and type(value['stop_requested']) is bool and (value['stop_requested'] == (value['reason'] == 'stop_requested')), 'stop')
        self.c._int(value['elapsed_ms'], 0, (a['seconds'] + 30) * 1000, 'budget')
        self.c._obj(value['cleanup'], self.c.CLEANUP_KEYS)
        self.c._need(all((x is True for x in value['cleanup'].values())), 'identity')
        running = self.c.validate_running(self._at(value['running'], root / 'running-v1.json'), a, admission_binding)
        for key in ('worker', 'server', 'launcher', 'guest', 'guest_ancestry'):
            self._equal(value[key], running[key])
        self._equal(req['owner'], running['owner'])
        base._auth(value['auth'], a['server'])
        self._equal(value['sources_after'], dict(sources=a['sources'], python=a['python'], tools=a['server']['tools'], auth=value['auth']))
        self._preflight(value['preflight'], root / 'server/preflight-v1.json')
        self._preflight(value['guest_preflight'], root / 'guest-preflight-v1.json', True)
        server_admission = self._pin(root / 'server/admission-v1.json')
        self._equal(self._json(server_admission), a['server'])
        history = ()
        for kind in ('version', 'devices'):
            p = base.validate_proof(self._pin(root / 'server' / ('proof-' + kind + '-v1.json')), a['server'], server_admission, expected_worker, value['server'], kind, completed_ports=history)
            history += (p['endpoint']['local_port'],)
        initial = env.read_json(root / 'server/readiness-v1.json')
        self.c._need(type(initial) is list and 1 <= len(initial) <= 200, 'observation')
        for i, item in enumerate(initial):
            self.c._obj(item, ('observation', 'tables'))
            if i < len(initial) - 1:
                base.validate_observation(item['observation'], None, None, None, require_empty=True)
            else:
                base.validate_observation(item['observation'], value['server'], None, None)
            base._tables(item['tables'], item['observation'])
        ready = self.c.validate_ready(self._at(value['ready'], root / 'target-ready-v1.json'), running, a)
        self._equal(value['ready'], running['ready'])
        self._equal(value['guest_job'], ready['guest_job'])
        self.c.validate_guest_job(self._json(value['guest_job']), running)
        registration = self._json(ready['queries'])
        self.c._need(self.c.validate_query_bundle(registration, running, expected_worker, admission_binding, None) == running['transport_id'], 'identity')
        self.verify_guest_inputs(value['guest_inputs'], a, admission_binding)
        boot = self._at(value['boot_claim'], Path(a['guest']['root']) / self.c.BOOT_CLAIM_FILE)
        self.c._obj(boot, ('version', 'protocol', 'admission', 'worker', 'proposal'))
        self.c._int(boot['version'], 1, 1)
        self.c._need(boot['protocol'] == self.c.PROTOCOL)
        self._equal(boot['admission'], admission_binding)
        self._equal(boot['worker'], expected_worker)
        self._equal(boot['proposal'], a['guest']['proposal'])
        readiness = self._at(value['readiness'], root / 'readiness-v1.json')
        self.c._need(type(readiness) is list and 1 <= len(readiness) <= 300, 'observation')
        last_ms = -1
        registration_count = 0
        last_stage = -1
        seen_stages = set()
        for entry in readiness:
            self.c._obj(entry, ('elapsed_ms', 'stage', 'observation', 'tables', 'queries'))
            self.c._int(entry['elapsed_ms'], 0, 180000, 'budget')
            self.c._need(entry['elapsed_ms'] >= last_ms, 'clock')
            last_ms = entry['elapsed_ms']
            self.c._need(entry['stage'] in ('guest_process', 'guest_ports', 'registration'))
            stage = ('guest_process', 'guest_ports', 'registration').index(entry['stage'])
            self.c._need(stage >= last_stage, 'clock')
            last_stage = stage
            seen_stages.add(stage)
            if entry['stage'] == 'guest_process':
                self.c._need(entry['observation'] is entry['tables'] is entry['queries'] is None)
            else:
                self.c.validate_guest_prefix(entry['observation'], running['guest'], running['server'])
                base._tables(entry['tables'], entry['observation'])
                if entry['stage'] == 'registration':
                    registration_count += 1
                    self.c._need(registration_count <= 60, 'budget')
                    q = self._json(entry['queries'])
                    self.c.validate_query_bundle(q, running, expected_worker, admission_binding, None, require_device=False)
                else:
                    self.c._need(entry['queries'] is None)
        self.c._need(seen_stages == {0, 1, 2} and readiness[-1]['stage'] == 'registration', 'observation')
        self._equal(readiness[-1]['queries'], ready['queries'])
        self._equal(readiness[-1]['observation'], ready['guest_observation'])
        self._equal(readiness[-1]['tables'], ready['guest_tables'])
        for key in ('server_returncode', 'guest_returncode'):
            self.c._int(value[key], -2 ** 31, 2 ** 32 - 1, 'identity')
        self._capture(value['server_capture'], root / 'server-output-v1', value['server'], value['server_returncode'])
        self._capture(value['guest_capture'], root / 'guest-output-v1', value['launcher'], value['guest_returncode'])
        terminal = self._at(value['guest_terminal'], root / 'guest-terminal-v1.json')
        self.c._obj(terminal, ('version', 'protocol', 'guest', 'terminate_attempted', 'wait_completed', 'returncode', 'handle_closed'))
        self.c._int(terminal['version'], 1, 1)
        self.c._need(terminal['protocol'] == self.c.PROTOCOL)
        self._equal(terminal['guest'], value['guest'])
        self.c._need(all((terminal[k] is True for k in ('terminate_attempted', 'wait_completed', 'handle_closed'))), 'identity')
        self.c._int(terminal['returncode'], -2 ** 31, 2 ** 32 - 1, 'identity')
        if value['stop_requested']:
            self.c.check_stop(self._json(self._pin(root / 'stop-v1.json')), admission_binding['sha256'])
        self.c.revalidate_inputs(a)
        return copy.deepcopy(value)

def _raw(pin, cap=2 * 1024 * 1024):
    return _Verifier(c)._raw(pin, cap)

def _json(pin):
    return _Verifier(c)._json(pin)

def _at(pin, path):
    return _Verifier(c)._at(pin, path)

def _pin(path):
    return _Verifier(c)._pin(path)

def _equal(a, b, reason='binding'):
    return _Verifier(c)._equal(a, b, reason)

def verify_proof(pin, session, context):
    return _Verifier(c).verify_proof(pin, session, context)

def verify_client_record(binding, session, admission):
    return _Verifier(c).verify_client_record(binding, session, admission)

def require_current_clients(root, count, session_binding, admission):
    return _Verifier(c).require_current_clients(root, count, session_binding, admission)

def _capture(pin, path, process, returncode):
    return _Verifier(c)._capture(pin, path, process, returncode)

def _preflight(pin, path, guest=False):
    return _Verifier(c)._preflight(pin, path, guest)

def verify_guest_inputs(pin, admission, admission_binding):
    return _Verifier(c).verify_guest_inputs(pin, admission, admission_binding)

def verify_owned_target_result(binding, admission, admission_binding, request_binding, expected_worker):
    return _Verifier(c).verify_owned_target_result(binding, admission, admission_binding, request_binding, expected_worker)

def _verify_proof(contract, pin, session, context):
    return _Verifier(contract).verify_proof(pin, session, context)

def _verify_client_record(contract, binding, session, admission):
    return _Verifier(contract).verify_client_record(binding, session, admission)

def _require_current_clients(contract, root, count, session_binding, admission):
    return _Verifier(contract).require_current_clients(root, count, session_binding, admission)

def _verify_owned_target_result(contract, *args, **kwargs):
    return _Verifier(contract).verify_owned_target_result(*args, **kwargs)
