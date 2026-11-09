"""Fixed SDK18 advisory preflight; never authorization, admission or SDK dispatch.

Import performs no I/O. CLI accepts no factory, path, profile or operation.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PureWindowsPath
import re
import socket
import sys
import time
from types import SimpleNamespace

B121 = Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-refusal-freeze-v1')
OUT = Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-refusal-readiness-v1')
REPORT = OUT / 'readiness-report-v1.json'
PROFILE_HEAD = 'dbcafb0070734cbccbd420a159f6305bc6f9090d'
LEDGER = Path('D:/Dev/_Migration/LocalLore-AVD-Storage/ledger-v1.json')
GUEST = Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-refusal-ui-v1/avd-v1')
GIB = 1024**3
UINT64 = 2**64-1


def _known_pin(path, size, sha):
    return dict(path=str(PureWindowsPath(path)), bytes=size, sha256=sha)


CATALOG = _known_pin(B121/'profile-source-publication-v1.json',755007,'aa58a83cd42933165f659b454d768b3b6c4cbc4458efabf300704e09fd50de31')
HANDOFF = _known_pin(B121/'inspection-v1/frozen-inputs-v1.json',9021,'23e13dc8ef2a9a7dc169dc88bb3ef013767c6e223a126f75ba8d2423c151e041')
PREPARE = _known_pin(B121/'inspection-v1/prepare-proposal-v1.json',173555,'4dc63f47db5ab969402f9bac170641c8b6e4a37c494974e047b2369d5f3691aa')
PARENT = _known_pin(B121/'candidate-source-v1/scripts/run_record_cancellation_operation.py',18339,'a6c365e795f7b1e2934cbb5aa038339459064967cb1d812e6cae4693703bc49d')
PARENT_RULES = _known_pin(B121/'candidate-source-v1/scripts/record_cancellation_operation_contract.py',4495,'2baa4b52a7991279004060c55b1535edde4afa67e8dd29b64f86578d42b79214')
RESOURCE_REASONS = frozenset(('host_capacity','host_commit_capacity','host_commit_unavailable','host_cpu_capacity','memory_unavailable','invalid_profile','windows_required'))
OWN_REASONS = frozenset(('resources_invalid','commit_invalid','ports_invalid','ports_unavailable','storage_invalid','storage_capacity','input_invalid','verification_failed','revalidation_failed','inputs_changed','report_exists'))


class ReadinessRefused(ValueError):
    """Finite host categories; exception payloads never enter the report."""


def _need(value, reason):
    if not value:
        raise ReadinessRefused(reason)


def _object(value, keys, reason):
    _need(type(value) is dict and all(type(k) is str for k in value) and set(value)==set(keys),reason)


def _uint(value, reason):
    _need(type(value) is int and 0<=value<=UINT64,reason)
    return value


def _pin(value, expected=None):
    _object(value,('path','bytes','sha256'),'input_invalid')
    path=value['path'];sha=value['sha256']
    _need(type(path) is str and len(path)<=1024 and not any(ord(c)<32 for c in path),'input_invalid')
    p=PureWindowsPath(path)
    _need(p.is_absolute() and p.drive.upper()=='D:' and str(p)==path,'input_invalid')
    _need(type(sha) is str and re.fullmatch('[0-9a-f]{64}',sha) is not None,'input_invalid')
    result=dict(path=path,bytes=_uint(value['bytes'],'input_invalid'),sha256=sha)
    _need(result['bytes']>0,'input_invalid')
    if expected is not None:
        _need(result==expected,'input_invalid')
    return result


def _stamp(value):
    _object(value,('profile_head','source_catalog','handoff','prepare','ledger'),'input_invalid')
    _need(type(value['profile_head']) is str and value['profile_head']==PROFILE_HEAD,'input_invalid')
    ledger=_pin(value['ledger']);_need(PureWindowsPath(ledger['path'])==PureWindowsPath(LEDGER),'input_invalid')
    return dict(profile_head=PROFILE_HEAD,source_catalog=_pin(value['source_catalog'],CATALOG),
        handoff=_pin(value['handoff'],HANDOFF),prepare=_pin(value['prepare'],PREPARE),ledger=ledger)


def _plan(value):
    _need(type(value) is dict and all(type(k) is str for k in value),'input_invalid')
    _need(type(value.get('memory_mib')) is int and value['memory_mib']==8192 and
          type(value.get('cores')) is int and value['cores']==4 and
          type(value.get('host_available_memory_min')) is int and value['host_available_memory_min']==12*GIB,'input_invalid')
    floors=value.get('host_free_min');_object(floors,('C:','D:'),'input_invalid')
    _need(type(floors['C:']) is int and floors['C:']==16*GIB and type(floors['D:']) is int and floors['D:']==40*GIB,'input_invalid')
    return json.loads(json.dumps(value,sort_keys=True,allow_nan=False))


def _commit(value):
    keys=('version','commit_total_bytes','commit_limit_bytes','available_commit_bytes','guest_memory_bytes','required_commit_bytes','reserve_bytes')
    _object(value,keys,'commit_invalid');v={k:_uint(value[k],'commit_invalid') for k in keys}
    _need(v['version']==1 and 0<v['commit_limit_bytes'] and v['commit_total_bytes']<=v['commit_limit_bytes'] and
          v['available_commit_bytes']==v['commit_limit_bytes']-v['commit_total_bytes'] and
          v['guest_memory_bytes']==8*GIB and v['reserve_bytes']==2*GIB and v['required_commit_bytes']==10*GIB and
          v['available_commit_bytes']>=v['required_commit_bytes'],'commit_invalid')
    return v


def _resources(value):
    _object(value,('free_bytes','available_memory','logical_cpus','commit_capacity'),'resources_invalid')
    free=value['free_bytes'];_object(free,('C:','D:'),'resources_invalid')
    result=dict(free_bytes={k:_uint(free[k],'resources_invalid') for k in ('C:','D:')},
        available_memory=_uint(value['available_memory'],'resources_invalid'),
        logical_cpus=_uint(value['logical_cpus'],'resources_invalid'),commit_capacity=_commit(value['commit_capacity']))
    _need(result['free_bytes']['C:']>=16*GIB and result['free_bytes']['D:']>=40*GIB and
          result['available_memory']>=12*GIB and result['logical_cpus']>=8,'resources_invalid')
    return result


def _commit_observation(api):
    keys=('version','commit_total_bytes','commit_limit_bytes','available_commit_bytes')
    value=api.commit_snapshot();_object(value,keys,'commit_invalid')
    snapshot={k:_uint(value[k],'commit_invalid') for k in keys}
    _need(snapshot['version']==1 and 0<snapshot['commit_limit_bytes'] and snapshot['commit_total_bytes']<=snapshot['commit_limit_bytes'] and
          snapshot['available_commit_bytes']==snapshot['commit_limit_bytes']-snapshot['commit_total_bytes'],'commit_invalid')
    facts=dict(snapshot,guest_memory_bytes=8*GIB,required_commit_bytes=10*GIB,reserve_bytes=2*GIB)
    try:
        value=api.commit_check(snapshot,8192)
    except KeyboardInterrupt:
        raise
    except BaseException as error:
        reason=_reason(error,api)
        capacity=type(error) is api.HostCommitRefused and reason=='commit_capacity' and snapshot['available_commit_bytes']<10*GIB
        return dict(passed=False,reason=reason,facts=facts if capacity else None)
    try:
        checked=_commit(value)
        _need(all(checked[k]==snapshot[k] for k in keys),'commit_invalid')
        return dict(passed=True,reason='ok',facts=checked)
    except KeyboardInterrupt:
        raise
    except BaseException as error:
        return dict(passed=False,reason=_reason(error,api),facts=None)


def _storage(value, stamp):
    _object(value,('scope','version','root','ledger','active_count','max_guests','budget_bytes','charged_bytes',
        'projected_bytes','reservation_bytes','would_fit','admission_granted','root_limit_exceeded','byte_limit_exceeded'),'storage_invalid')
    _need(value.get('scope')=='receipt-avd-prepare-capacity-preview-v1' and type(value.get('version')) is int and value['version']==1 and
          type(value.get('root')) is str and PureWindowsPath(value['root'])==PureWindowsPath(GUEST),'storage_invalid')
    _need(_pin(value.get('ledger'))==stamp['ledger'],'inputs_changed')
    names=('active_count','max_guests','budget_bytes','charged_bytes','projected_bytes','reservation_bytes')
    result={k:_uint(value.get(k),'storage_invalid') for k in names}
    for k in ('would_fit','admission_granted','root_limit_exceeded','byte_limit_exceeded'):
        _need(type(value.get(k)) is bool,'storage_invalid')
    _need(value['admission_granted'] is False and result['max_guests']==2 and result['budget_bytes']==64*GIB and
          result['reservation_bytes']==40*GIB and result['projected_bytes']==result['charged_bytes']+40*GIB,'storage_invalid')
    fits=result['active_count']<2 and result['projected_bytes']<=64*GIB
    _need(value['root_limit_exceeded']==(result['active_count']>=2) and value['byte_limit_exceeded']==(result['projected_bytes']>64*GIB) and value['would_fit']==fits,'storage_invalid')
    result.update(would_fit=fits,admission_granted=False)
    return result


def _reason(error, api):
    classes=((ReadinessRefused,OWN_REASONS),(api.EnvironmentRefused,RESOURCE_REASONS),
        (api.HostCommitRefused,frozenset(('commit_capacity','commit_invalid','commit_unavailable'))),
        (api.StorageRefused,frozenset(('registry_locked','storage_capacity_exceeded'))))
    for cls,codes in classes:
        if type(error) is cls:
            args=error.args
            if len(args)==1 and type(args[0]) is str and args[0] in codes:
                return args[0]
    return 'observation_failed'


def _empty():
    return dict(version=1,scope='sdk18-record-refusal-readiness-v1',ready=False,execution_authorized=False,
        feature_acceptance=False,inputs_stable=False,phase='verification_failed',reason='verification_failed',
        checks={k:dict(passed=False,reason='not_observed',facts=None) for k in ('resources','commit','ports','storage')},
        bindings=None,sequential_observations=True,observed_unix_ns=time.time_ns(),elapsed_ms=0)


def _done(result,start):
    result['elapsed_ms']=round(max(0,time.monotonic()-start)*1000)
    return result


def _probe(api):
    """Private memory-port seam. CLI always uses the fixed genuine loader."""
    start=time.monotonic();result=_empty()
    try:
        plan,stamp=api.verify();plan=_plan(plan);stamp=_stamp(stamp);result['bindings']=stamp
    except KeyboardInterrupt:
        result.update(phase='cancelled',reason='cancelled');return _done(result,start)
    except BaseException:
        return _done(result,start)
    steps=(('resources',lambda:_resources(api.resource_facts(plan))),
        ('commit',lambda:_commit_observation(api)),
        ('ports',lambda:_ports_result(api.check_ports())),
        ('storage',lambda:_storage(api.preview_prepare(),stamp)))
    for name,observe in steps:
        try:
            facts=observe()
            if name=='commit':result['checks'][name]=facts
            else:
                passed=not(name=='storage' and facts['would_fit'] is False)
                result['checks'][name]=dict(passed=passed,reason='ok' if passed else 'storage_capacity',facts=facts)
        except KeyboardInterrupt:
            result['checks'][name]=dict(passed=False,reason='cancelled',facts=None)
            result.update(phase='cancelled',reason='cancelled',elapsed_ms=round(max(0,time.monotonic()-start)*1000));return result
        except BaseException as error:
            result['checks'][name]=dict(passed=False,reason=_reason(error,api),facts=None)
    try:
        after_plan,after_stamp=api.verify()
    except KeyboardInterrupt:
        result.update(phase='cancelled',reason='cancelled');return _done(result,start)
    except BaseException:
        result.update(reason='revalidation_failed');return _done(result,start)
    try:
        _need(_plan(after_plan)==plan and _stamp(after_stamp)==stamp,'inputs_changed')
        result['inputs_stable']=True
    except KeyboardInterrupt:
        result.update(phase='cancelled',reason='cancelled');return _done(result,start)
    except BaseException:
        result.update(reason='inputs_changed');return _done(result,start)
    result['ready']=all(v['passed'] for v in result['checks'].values())
    result.update(phase='completed',reason='ready' if result['ready'] else next(v['reason'] for v in result['checks'].values() if not v['passed']),
        elapsed_ms=round(max(0,time.monotonic()-start)*1000))
    return result


def _ports_result(value):
    _need(value is None,'ports_invalid')
    return dict(guest_ports=[5592,5593],private_adb_port=15937)


def _ports(env):
    env.ports_free();opened=[];error=None
    try:
        for family,address in ((socket.AF_INET,'127.0.0.1'),(socket.AF_INET6,'::1')):
            s=socket.socket(family,socket.SOCK_STREAM);opened.append(s)
            s.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
            if family==socket.AF_INET6:s.setsockopt(socket.IPPROTO_IPV6,socket.IPV6_V6ONLY,1)
            s.bind((address,15937))
    except BaseException as caught:
        error=caught
    finally:
        for s in opened:
            try:s.close()
            except BaseException as caught:
                if error is None or isinstance(caught,KeyboardInterrupt):error=caught
    if error is not None:
        if isinstance(error,Exception):raise ReadinessRefused('ports_unavailable') from None
        raise error


def _physical(path):
    for p in (path,*path.parents):
        _need(p.resolve(strict=True)==p and not p.is_symlink() and not getattr(p.lstat(),'st_file_attributes',0)&1024,'input_invalid')


def _fixed(pin):
    path=Path(pin['path']);_physical(path)
    _need(path.is_file() and path.stat().st_nlink==1 and path.stat().st_size==pin['bytes'] and pin['bytes']<=2*1024**2,'input_invalid')
    with path.open('rb') as stream:raw=stream.read(pin['bytes']+1)
    _need(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'input_invalid')
    _physical(path);return raw


def _api():
    raw=_fixed(PARENT);_fixed(PARENT_RULES)
    spec=importlib.util.spec_from_file_location('_sdk18_readiness_parent',PARENT['path']);parent=importlib.util.module_from_spec(spec)
    exec(compile(raw,PARENT['path'],'exec'),parent.__dict__)
    outer,loaded=parent._parts();fresh,parts=loaded.fresh._parts()
    def verify():
        _fixed(PARENT);_fixed(PARENT_RULES);_fixed(CATALOG);_fixed(HANDOFF);_fixed(PREPARE)
        loaded.fresh.source_snapshot()
        h=fresh.validate_handoff(loaded.fresh.read(HANDOFF));plan=loaded.fresh.read(PREPARE)
        parts.env.validate_proposal(plan,'prepare')
        _need(plan['paths']['root']==str(GUEST) and plan['allow_environment_calls'] is False and plan['root_go_pending'] is True,'input_invalid')
        _need(fresh.same(h['sources'],parts.contract.source_bindings()) and fresh.same(h['python'],parts.probe._python_bindings()),'input_invalid')
        loaded.fresh._installed(h)
        parts.env.verify_installation(plan);parts.env.check_external_state(plan)
        manifest=parts.build.verify_frozen_product(h['artifacts'])
        _need(fresh.same(loaded.fresh.read(h['artifacts']['build']),manifest),'input_invalid')
        for p in (fresh.GUEST,fresh.RUNTIME,fresh.CONTROLS,fresh.LIVE,outer.LIVE):
            _need(not os.path.lexists(p),'input_invalid')
        return plan,dict(profile_head=fresh.SOURCE_HEAD,source_catalog=CATALOG,handoff=HANDOFF,prepare=PREPARE,ledger=parts.env.binding(LEDGER))
    return SimpleNamespace(verify=verify,resource_facts=parts.env.resource_facts,
        commit_snapshot=parts.env.commit_capacity.read_commit,commit_check=parts.env.commit_capacity.require_capacity,
        check_ports=lambda:_ports(parts.env),preview_prepare=lambda:parts.storage.preview_prepare(GUEST),
        EnvironmentRefused=parts.env.EnvironmentRefused,HostCommitRefused=parts.env.commit_capacity.HostCommitRefused,StorageRefused=parts.storage.StorageRefused)


def main(argv=None):
    if (sys.argv[1:] if argv is None else argv)!=['inspect']:return 2
    start=time.monotonic()
    try:
        _physical(OUT);_need(OUT.drive.upper()=='D:' and not os.path.lexists(REPORT),'report_exists')
        try:result=_probe(_api())
        except KeyboardInterrupt:result=_empty();result.update(phase='cancelled',reason='cancelled')
        except BaseException:result=_empty()
        _done(result,start)
        raw=(json.dumps(result,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode('ascii')
        _need(len(raw)<=16384,'input_invalid')
        with REPORT.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        print(json.dumps(dict(scope=result['scope'],ready=result['ready'],execution_authorized=False,report=_known_pin(REPORT,len(raw),hashlib.sha256(raw).hexdigest()))))
        return 0 if result['ready'] else 1
    except BaseException:
        print('SDK18 readiness refused',file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
