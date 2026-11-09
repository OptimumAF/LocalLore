"""Original SDK16 prepare-input inspection tests; no target execution.

Synthetic metadata and tiny retained D files exercise publication and failure
boundaries. Installed SDK/profile and build observations are explicit test ports.
No test grants preparation, admission, retirement, or boot authority.
"""
from contextlib import ExitStack, redirect_stdout
import copy
import ctypes
import io
import json
import os
from pathlib import Path, PureWindowsPath
import socket
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import benchmarks
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage
from benchmarks import owned_knowledge_ui_contract as profile
from scripts import freeze_knowledge_ui_prepare_inputs as tool

SOURCE = Path('D:/Worktrees/LocalLore-original-input-compose-review-v1')
SOURCE_HEAD = '80f2c10cceb7fb061bb0ab9ddfa50c7e17fd99f2'
HOME = Path('D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-prepare-inputs-v1/test-agent-v1')
GUEST = Path('D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-ui-v1/avd-v1')
FILES = {'knowledge-build-v1.json','prepare-proposal-v1.json','capacity-preview-v1.json',
         'handoff-inputs-v1.json','result-v1.json'}
MISSING = ('exact_retirement_prepare_and_boot_approval','pinned_storage_retirement',
 'fresh_prepare_authorization','guarded_prepare_result',
 'fresh_run_proposal_authorization_and_admission','fresh_ownership_resources_ports')


class KnowledgePrepareDefinitionTests(unittest.TestCase):
    def test_import_has_no_io_and_frozen_operational_constants_are_exact(self):
        path=Path(tool.__file__);raw=path.read_bytes()
        with ExitStack() as stack:
            for name in ('open','stat','lstat','mkdir','resolve'):
                stack.enter_context(patch.object(Path,name,side_effect=AssertionError('Import IO')))
            stack.enter_context(patch.object(subprocess,'run',side_effect=AssertionError('Import process')))
            stack.enter_context(patch.object(subprocess,'Popen',side_effect=AssertionError('Import process')))
            stack.enter_context(patch.object(ctypes,'WinDLL',create=True,side_effect=AssertionError('Import native')))
            namespace={'__name__':'knowledge_inspection_definitions_only','__file__':str(path)}
            exec(compile(raw,str(path),'exec'),namespace)
        self.assertEqual(namespace['SOURCE'],SOURCE)
        self.assertEqual(namespace['SOURCE_HEAD'],SOURCE_HEAD)
        self.assertEqual(namespace['GUEST'],GUEST)
        self.assertEqual(namespace['OPERATOR'],path.parents[1])
        self.assertEqual(namespace['HELPER'],path)
        self.assertEqual(namespace['OUTPUT'],namespace['OUT']/'frozen-inputs-v1')
        self.assertEqual(tuple(namespace['MISSING']),MISSING)

    def test_cli_cannot_select_an_output_registry_guest_source_or_execute_action(self):
        for argv in (['--output','D:/unselected'],['--registry','D:/unselected'],
                     ['--source','D:/unselected'],['prepare'],['run'],['--guest',str(GUEST)]):
            with self.subTest(argv=argv),patch.object(tool,'inspect') as observe,redirect_stdout(io.StringIO()):
                try:code=tool.main(argv)
                except SystemExit as error:code=error.code
                self.assertIs(type(code),int);self.assertNotEqual(code,0)
                observe.assert_not_called()


def budget():
    total=sum(p.stat().st_size for p in HOME.rglob('*') if p.is_file()) if HOME.exists() else 0
    if total+1024*1024>64*1024*1024:raise RuntimeError('fixture_budget_refused')


class Graph:
    """Real tiny byte bindings, explicit synthetic installed/build/profile ports."""
    def __init__(self, fits=False, initializer=False):
        budget();HOME.mkdir(parents=True,exist_ok=True)
        self.root=Path(tempfile.mkdtemp(prefix='inspect-',dir=HOME));assert self.root.drive.upper()=='D:'
        self.source=self.root/'source';self.operator=self.root/'operator';self.out=self.root/'out'
        self.output=self.out/'frozen-inputs-v1';self.guest=self.root/'guest-parent/avd-v1'
        self.registry=self.root/'registry';self.sdk=self.root/'sdk';self.java=self.root/'java'
        for d in (self.source/'benchmarks',self.operator/'scripts',self.out,self.guest.parent,self.registry,self.sdk,self.java,self.root/'originals'):d.mkdir(parents=True,exist_ok=True)
        self.helper=self.operator/'scripts/freeze_knowledge_ui_prepare_inputs.py';self.helper.write_bytes(b'SYNTHETIC immutable helper binding only')
        names=set(profile.SOURCE_NAMES)|({'__init__.py'} if initializer else set())
        for name in sorted(names):(self.source/'benchmarks'/name).write_bytes(('SYNTHETIC source '+name).encode())
        self.sources=[env.binding(self.source/'benchmarks'/n) for n in sorted(names)]
        def marker(name,raw=b'SYNTHETIC inert file; never execute'):
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);return env.binding(path)
        self.python=dict(executable=marker('python.exe'),runtime_dll=marker('python314.dll'))
        self.apks=dict(product_apk=marker('product-not-apk.bin'),test_apk=marker('tests-not-apk.bin'))
        self.manifest=dict(version=1,scope='knowledge-ui-build-v1',mode='fixed-b88-byte-attestation-v1',product={},artifacts=copy.deepcopy(self.apks),current_native_bindings={},evidence={},facts={},instrumentations=[list(r) for r in profile.INSTRUMENTATIONS])
        self.build_path=self.root/'original-b88-manifest.json';env.create_json(self.build_path,self.manifest);self.build_pin=env.binding(self.build_path)
        self.ledger=self.registry/'ledger-v1.json';env.create_json(self.ledger,{'synthetic_snapshot_port':True});self.before_ledger=self.ledger.read_bytes()
        self.token=marker('console-token',b'SYNTHETIC_CREDENTIAL_BYTES_UNPUBLISHED')
        self.old=dict(registry=str(self.root/'old-avd'),exists=False,names=[],files=[])
        required=['receipt_avd_environment.py','runtime_spike.py','host_commit_capacity.py','receipt_avd_storage.py','prepare_recovery_contract.py']
        self.installed=[env.binding(self.source/'benchmarks'/n) for n in required]
        self.installed += [marker(n) for n in ('sdk/platform-tools/adb.exe','sdk/emulator/emulator.exe','sdk/cmdline-tools/latest/bin/avdmanager.bat','sdk/system-images/android-35/google_apis/x86_64/data/empty_data_disk','java/release')]
        charge=0 if fits else 25*1024**3;active=0 if fits else 2
        self.capacity=dict(version=1,scope='receipt-avd-prepare-capacity-preview-v1',root=str(self.guest),ledger=env.binding(self.ledger),max_guests=2,budget_bytes=64*1024**3,reservation_bytes=40*1024**3,active_count=active,charged_bytes=charge,projected_bytes=charge+40*1024**3,root_limit_exceeded=active==2,byte_limit_exceeded=not fits,would_fit=fits,admission_granted=False)
        self.writes=[];self.forbidden=[];self.before_write=lambda *_:None;self.after_write=lambda *_:None
        self.changing=False;self.mutation_number=0;self.source_head=SOURCE_HEAD;self.operator_head='1'*40
        self.git_hook=lambda *_:None;self.git_calls=[];self.plan_changes={};self.plan_error=None
        def forbid(name):
            call=Mock(side_effect=AssertionError('Forbidden mechanism: '+name));self.forbidden.append(call);return call
        self.api_env=SimpleNamespace(encoded=env.encoded,binding=env.binding,check_binding=env.check_binding,read_json=env.read_json,safe_path=env.safe_path,create_json=self.create,plan_prepare=Mock(side_effect=self.plan),validate_proposal=env.validate_proposal,verify_installation=Mock(side_effect=self.verify_installation),check_external_state=Mock(side_effect=self.external))
        for name in ('prepare','_prepare_proposal_value','authorize','check_authorization','plan_run','resource_facts','ports_free','supervise','process_identity','verify_prepared'):setattr(self.api_env,name,forbid(name))
        self.api_storage=SimpleNamespace(DEFAULT_REGISTRY=self.registry,safe_path=storage.safe_path,binding=storage.binding,preview_prepare=Mock(side_effect=lambda *_:copy.deepcopy(self.capacity)))
        for name in ('reserve_prepare','record_state','record_closed','record_retired','_locked','_atomic_write','_initialize_registry'):setattr(self.api_storage,name,forbid(name))
        self.contract=SimpleNamespace(SOURCE_NAMES=profile.SOURCE_NAMES,binding=profile.binding,GUEST_ROOT=self.guest,INSTRUMENTATIONS=profile.INSTRUMENTATIONS,source_bindings=Mock(side_effect=lambda:copy.deepcopy(self.sources)))
        self.activation=SimpleNamespace(SOURCE_ROOT=self.source,CONTROLS=self.root/'never-controls',RUNTIME=self.root/'never-runtime')
        self.build=SimpleNamespace(create_manifest=Mock(side_effect=lambda:copy.deepcopy(self.manifest)),verify_frozen_product=Mock(side_effect=self.verify_build))
        self.probe=SimpleNamespace(_python_bindings=Mock(side_effect=lambda:copy.deepcopy(self.python)))
        self.api=SimpleNamespace(env=self.api_env,storage=self.api_storage,contract=self.contract,activation=self.activation,build=self.build,probe=self.probe)

    def create(self,path,value):
        path=Path(path);assert path.parent==self.output and path.name in FILES
        self.before_write(path.name,value);self.writes.append(path.name);env.create_json(path,value)
        self.after_write(path.name,path,value)

    def plan(self,root,sdk,java,output,**flags):
        assert (root,sdk,java)==(self.guest,self.sdk,self.java)
        assert flags==dict(real_candidate=True,four_core_candidate=True)
        if self.plan_error:raise self.plan_error
        value=dict(version=1,phase='prepare',avd_name=env.NAME,serial='emulator-5592',console_port=5592,sdk=str(sdk),java_home=str(java),paths=env.paths(root),adb_path=str(sdk/'platform-tools/adb.exe'),token=copy.deepcopy(self.token),old_avd=copy.deepcopy(self.old),bindings=copy.deepcopy(self.installed),userdata_mib=12288,sdcard_mib=8192,memory_mib=8192,cores=4,host_free_min=env.root_free_min(root),host_available_memory_min=12*1024**3,allow_environment_calls=False,root_go_pending=True)
        value.update(self.plan_changes);self.create(output,value);return value

    def verify_installation(self,value):
        assert {v['path'] for v in value['bindings']}=={v['path'] for v in self.installed}
        for item in value['bindings']:env.check_binding(item)

    def external(self,value):
        assert value['old_avd']==self.old
        env.check_binding(value['token'])

    def verify_build(self,artifacts):
        assert artifacts==dict(build=self.build_pin,**self.apks), 'Output copy is not original build authority'
        for value in artifacts.values():env.check_binding(value)
        return copy.deepcopy(self.manifest)

    def mutate(self,path,raw):
        self.changing=True
        try:
            self.mutation_number+=1
            (self.root/'originals'/('%03d-'%self.mutation_number+path.name)).write_bytes(path.read_bytes())
            path.write_bytes(raw)
        finally:self.changing=False

    def git(self,root,head=None):
        self.git_calls.append((root,head));self.git_hook(root,len(self.git_calls))
        actual=self.source_head if root==self.source else self.operator_head
        if len(actual)!=40 or (head is not None and actual!=head):raise tool.InspectionRefused('source')
        return actual

    def ports(self):
        stack=ExitStack();original_open=Path.open;original_mkdir=Path.mkdir
        for name,value in dict(SOURCE=self.source,OPERATOR=self.operator,HELPER=self.helper,__file__=str(self.helper),OUT=self.out,OUTPUT=self.output,GUEST=self.guest,REGISTRY=self.registry,SDK=self.sdk,JAVA=self.java,BUILD=self.build_path,BUILD_PIN=self.build_pin).items():stack.enter_context(patch.object(tool,name,value))
        stack.enter_context(patch.object(tool,'_api',return_value=self.api));stack.enter_context(patch.object(tool,'_git',side_effect=self.git))
        stack.enter_context(patch.object(Path,'cwd',return_value=self.source))
        stack.enter_context(patch.dict(os.environ,{k:'D:/Dev/_Temp' for k in ('TEMP','TMP','TMPDIR')}))
        # Existing metadata validation is real; only inherited OS-profile lookup
        # and module/file provenance are redirected into this isolated fixture.
        for module,name in ((env,'receipt_avd_environment.py'),(env.host,'runtime_spike.py'),(env.commit_capacity,'host_commit_capacity.py'),(env.guest_storage,'receipt_avd_storage.py')):stack.enter_context(patch.object(module,'__file__',str(self.source/'benchmarks'/name)))
        stack.enter_context(patch.object(env,'token_path',return_value=self.token['path']))
        def opened(path,mode='r',*args,**kwargs):
            if any(c in mode for c in 'wax+'):
                assert self.changing and path.is_relative_to(self.root) or path.parent==self.output and path.name in FILES,'Foreign write'
            return original_open(path,mode,*args,**kwargs)
        def mkdir(path,*args,**kwargs):
            assert path==self.output,'Foreign mkdir';return original_mkdir(path,*args,**kwargs)
        stack.enter_context(patch.object(Path,'open',opened));stack.enter_context(patch.object(Path,'mkdir',new=mkdir))
        for target,name in ((subprocess,'run'),(subprocess,'Popen'),(ctypes,'WinDLL'),(socket,'socket'),(storage,'_locked'),(storage,'_atomic_write'),(env,'_prepare_proposal_value'),(env,'prepare'),(env,'authorize'),(env,'resource_facts'),(env,'ports_free')):
            stack.enter_context(patch.object(target,name,create=name=='WinDLL',side_effect=AssertionError('Native/SDK/ledger operation')))
        return stack

    def check_unchanged(self,test):
        test.assertEqual(self.ledger.read_bytes(),self.before_ledger)
        test.assertFalse(self.guest.exists());test.assertFalse(self.activation.CONTROLS.exists());test.assertFalse(self.activation.RUNTIME.exists())
        for call in self.forbidden:call.assert_not_called()
        budget()


@unittest.skipUnless(os.name=='nt','Tiny retained physical D files; installed/native/build observations are test ports')
class KnowledgePrepareInputTests(unittest.TestCase):
    def run_graph(self,g):
        with g.ports():result=tool.inspect()
        g.check_unchanged(self);return result

    def test_blocked_capacity_still_emits_exact_five_review_records_without_authority(self):
        g=Graph();result=self.run_graph(g)
        self.assertEqual({p.name for p in g.output.iterdir()},FILES)
        self.assertIs(result['passed'],True);self.assertIs(result['capacity_blocked'],True)
        for flag in ('execution_authorized','preparation_performed','guest_created','ledger_written','admission_created','target_executed'):self.assertIs(result[flag],False)
        self.assertEqual(result['missing_requirements'],list(MISSING));self.assertEqual(result['method_count'],4)
        handoff=env.read_json(g.output/'handoff-inputs-v1.json')
        self.assertEqual(handoff['artifacts']['build'],g.build_pin)
        self.assertNotEqual(handoff['artifacts']['build'],handoff['build_copy'])
        self.assertEqual(env.read_json(handoff['build_copy']['path']),g.manifest)
        self.assertEqual(g.api_env.plan_prepare.call_count,1)
        self.assertNotIn(b'SYNTHETIC_CREDENTIAL_BYTES_UNPUBLISHED',b''.join(p.read_bytes() for p in g.output.iterdir()))

    def test_fitting_snapshot_and_optional_initializer_still_cannot_authorize_execution(self):
        g=Graph(fits=True,initializer=True);result=self.run_graph(g)
        self.assertEqual(result['source_count'],29);self.assertIs(result['capacity_would_fit'],True)
        self.assertIs(result['capacity_blocked'],False);self.assertIs(result['execution_authorized'],False)
        self.assertEqual(result['missing_requirements'],list(MISSING))

    def test_handoff_rejects_unknown_keys_boolean_aliases_foreign_paths_and_missing_gates(self):
        g=Graph();self.run_graph(g);good=env.read_json(g.output/'handoff-inputs-v1.json')
        with g.ports():
            self.assertEqual(tool.validate_handoff(good),good)
            for key,bad in (('version',True),('scope','sdk15-post-recovery-inputs-v1'),('operator_head','bad'),('execution_authorized',True),('model_material',True),('missing_requirements',[]),('guest',str(GUEST)),('source_head','0'*40)):
                value=copy.deepcopy(good);value[key]=bad
                with self.subTest(key=key),self.assertRaises(tool.InspectionRefused):tool.validate_handoff(value)
            value=copy.deepcopy(good);value['extra']='not permitted'
            with self.assertRaises(tool.InspectionRefused):tool.validate_handoff(value)
            for field in ('cores','memory_mib','max_run_seconds'):
                value=copy.deepcopy(good);value['profile'][field]=True
                with self.subTest(profile=field),self.assertRaises(tool.InspectionRefused):tool.validate_handoff(value)

    def test_foreign_or_boolean_capacity_metadata_refuses_before_any_output(self):
        for key,bad in (('root','D:/unselected'),('version',True),('active_count',True),('reservation_bytes',1),('would_fit',True),('admission_granted',True),('root_limit_exceeded',False)):
            g=Graph();g.capacity[key]=bad
            with self.subTest(key=key),g.ports(),self.assertRaises(tool.InspectionRefused):tool.inspect()
            self.assertFalse(g.output.exists());g.check_unchanged(self)

    def test_wrong_environment_heads_or_existing_output_refuse_without_overwriting(self):
        for fault in ('cwd','temp','source','operator','parent','output'):
            g=Graph();marker=None
            if fault=='source':g.source_head='0'*40
            elif fault=='operator':g.operator_head='not-a-head'
            elif fault=='parent':g.guest=g.root/'missing-parent/avd-v1';g.contract.GUEST_ROOT=g.guest
            elif fault=='output':g.output.mkdir();marker=g.output/'old.bin';marker.write_bytes(b'preserved failed output')
            with self.subTest(fault=fault),g.ports():
                with ExitStack() as extra:
                    if fault=='cwd':extra.enter_context(patch.object(Path,'cwd',return_value=g.operator))
                    if fault=='temp':extra.enter_context(patch.dict(os.environ,{'TMP':'C:/not-permitted'}))
                    with self.assertRaises((tool.InspectionRefused,env.EnvironmentRefused,storage.StorageRefused)):tool.inspect()
            if marker:self.assertEqual(marker.read_bytes(),b'preserved failed output')
            g.api_env.plan_prepare.assert_not_called();g.check_unchanged(self)

    def test_missing_foreign_or_stale_sources_and_python_are_not_frozen(self):
        for fault in ('missing','foreign','source_bytes','python_bytes'):
            g=Graph()
            if fault=='missing':g.sources.pop()
            elif fault=='foreign':g.sources[0]=dict(g.sources[0],path=str(g.root/'outside.py'))
            elif fault=='source_bytes':g.mutate(Path(g.sources[0]['path']),b'changed synthetic source')
            else:g.mutate(Path(g.python['runtime_dll']['path']),b'changed synthetic python')
            with self.subTest(fault=fault),g.ports(),self.assertRaises((tool.InspectionRefused,env.EnvironmentRefused,storage.StorageRefused)):tool.inspect()
            self.assertFalse(g.output.exists());g.check_unchanged(self)

    def test_prepare_profile_or_permission_drift_cannot_become_a_handoff(self):
        for key,bad in (('phase','run'),('memory_mib',8191),('cores',True),('userdata_mib',8192),('sdcard_mib',4096),('console_port',5594),('allow_environment_calls',True),('root_go_pending',False)):
            g=Graph();g.plan_changes[key]=bad
            with self.subTest(key=key),g.ports(),self.assertRaises((tool.InspectionRefused,env.EnvironmentRefused,storage.StorageRefused)):tool.inspect()
            self.assertFalse((g.output/'handoff-inputs-v1.json').exists());g.check_unchanged(self)

    def test_changed_original_build_binding_is_not_replaced_by_output_copy(self):
        g=Graph();g.mutate(g.build_path,g.build_path.read_bytes()+b' ')
        with g.ports(),self.assertRaises((tool.InspectionRefused,env.EnvironmentRefused)):tool.inspect()
        self.assertFalse(g.output.exists());g.check_unchanged(self)
        g=Graph();g.manifest['instrumentations'][-1]=g.manifest['instrumentations'][0]
        with g.ports(),self.assertRaises(tool.InspectionRefused):tool.inspect()
        self.assertFalse(g.output.exists())

    def test_partial_publication_is_preserved_create_once_and_cli_sanitizes_private_error(self):
        g=Graph();g.plan_error=OSError('PRIVATE_PLAN_CANARY')
        output=io.StringIO()
        with g.ports(),redirect_stdout(output):self.assertEqual(tool.main([]),1)
        self.assertNotIn('PRIVATE_PLAN_CANARY',output.getvalue())
        self.assertEqual({p.name for p in g.output.iterdir()},{'knowledge-build-v1.json'})
        before=(g.output/'knowledge-build-v1.json').read_bytes()
        with g.ports(),self.assertRaises(tool.InspectionRefused):tool.inspect()
        self.assertEqual((g.output/'knowledge-build-v1.json').read_bytes(),before)
        self.assertEqual(g.api_env.plan_prepare.call_count,1);g.check_unchanged(self)

    def test_late_sources_python_ledger_sdk_external_and_written_results_are_rechecked(self):
        for fault in ('source','python','ledger','sdk','token','build_copy','proposal_copy','capacity_copy','handoff_copy','result_copy'):
            g=Graph();changed=[]
            def after(name,path,value):
                target={'build_copy':'knowledge-build-v1.json','proposal_copy':'prepare-proposal-v1.json','capacity_copy':'capacity-preview-v1.json','handoff_copy':'handoff-inputs-v1.json','result_copy':'result-v1.json'}.get(fault,'handoff-inputs-v1.json')
                if name!=target or changed:return
                changed.append(fault)
                if fault=='source':p=Path(g.sources[0]['path'])
                elif fault=='python':p=Path(g.python['runtime_dll']['path'])
                elif fault=='ledger':p=g.ledger
                elif fault=='sdk':p=Path(g.installed[-1]['path'])
                elif fault=='token':p=Path(g.token['path'])
                else:p=path
                g.mutate(p,p.read_bytes()+b' ' if fault in ('source','python','ledger','sdk','token') else env.encoded({'freshly_rebound_but_wrong':True}))
            g.after_write=after
            with self.subTest(fault=fault),g.ports(),self.assertRaises((tool.InspectionRefused,env.EnvironmentRefused,storage.StorageRefused)):tool.inspect()
            self.assertEqual(changed,[fault])
            # Deliberate test ledger drift is the exception to unchanged ledger;
            # no storage transition/admission call is allowed in any case.
            for call in g.forbidden:call.assert_not_called()
