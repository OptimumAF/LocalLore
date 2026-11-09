"""Retained tiny B94 metadata; real shared validators, fake SDK observations.

No fixture executes a target, changes the shared registry or removes evidence.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import ExitStack
import copy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import uuid

from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage
from benchmarks import prepare_recovery_contract as history
from scripts import knowledge_ui_fresh_contract as rules
from scripts import run_knowledge_ui_fresh as bridge


HOME=Path('D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-fresh-bridge-v1/test-agent-v1/fixtures')


class FreshGraph:
    def __enter__(self):
        self.stack=ExitStack();self.events=[]
        HOME.mkdir(parents=True,exist_ok=True)
        assert HOME.resolve().drive.upper()=='D:'
        self.base=HOME/uuid.uuid4().hex;self.base.mkdir()
        self.live=self.base/'live';self.live.mkdir()
        self.guest=self.base/'guest';self.guest.mkdir()
        self.registry=self.base/'registry';self.registry.mkdir()
        self.source=self.base/'source';(self.source/'benchmarks').mkdir(parents=True)
        self.operator=self.base/'operator';(self.operator/'scripts').mkdir(parents=True)
        self.inspector_root=self.base/'inspector';self.inspector_root.mkdir()
        self.runtime=self.base/'runtime';self.controls=self.base/'controls'
        self.token=self.base/'synthetic-token';self.token.write_bytes(b'SYNTHETIC not a credential')
        self.stack.enter_context(patch.object(env,'token_path',return_value=str(self.token)))
        values=dict(SOURCE=self.source,INSPECTOR_ROOT=self.inspector_root,OPERATOR_ROOT=self.operator,
            OPERATOR=self.operator/'scripts/run_knowledge_ui_fresh.py',CONTRACT=self.operator/'scripts/knowledge_ui_fresh_contract.py',
            OUT=self.base,LIVE=self.live,PROPOSAL=self.base/'PROPOSED_OPERATION.md',AUTHORITY=self.base/'human-authority-v1.json',
            ATTEMPT=self.live/'attempt-v1.json',REGISTRY=self.registry,GUEST=self.guest,RUNTIME=self.runtime,CONTROLS=self.controls,
            RUN_PROPOSAL=self.live/'run-proposal-v1.json',RUN_AUTHORIZATION=self.live/'run-authorization-v1.json',
            PREPARE_AUTHORIZATION=self.live/'prepare-authorization-v1.json',ADMISSION=self.runtime/'admission-v1.json',INPUT=self.controls/'run-input-v1.json')
        for name,value in values.items():self.stack.enter_context(patch.object(rules,name,value))
        self.stack.enter_context(patch.object(bridge,'ROOT',self.operator))
        self.stack.enter_context(patch.object(bridge,'__file__',str(rules.OPERATOR)))
        for path in (rules.OPERATOR,rules.CONTRACT,rules.PROPOSAL):path.write_bytes(b'SYNTHETIC fixed source only')
        self.sources=[]
        for name in ('knowledge_ui_activation.py','core_fixture.py'):
            p=self.source/'benchmarks'/name;p.write_bytes(b'SYNTHETIC source '+name.encode());self.sources.append(env.binding(p))
        self.sources.sort(key=lambda p:p['path'])
        self.manifest=dict(version=1,scope='synthetic-b88-observation',instrumentations=[['synthetic','one']])
        self.build_path=self.base/'original-build.json';self.write(self.build_path,self.manifest)
        self.product=self.base/'product.apk';self.product.write_bytes(b'SYNTHETIC not an APK')
        self.test=self.base/'test.apk';self.test.write_bytes(b'SYNTHETIC not an APK')
        self.build_copy=self.base/'build-copy.json';self.write(self.build_copy,self.manifest)
        self.prepare_path=self.base/'prepare-proposal.json';self.proposal=self.make_proposal();self.write(self.prepare_path,self.proposal)
        self.prepare_pin=env.binding(self.prepare_path)
        self.make_prepared_files()
        self.entry=dict(root=str(self.guest),proposal_sha256=self.prepare_pin['sha256'],state='prepared',reserved_bytes=40*1024**3,
            closure=None,retirement=None,retirement_receipt=None,recovery=None)
        self.ledger=dict(version=2,max_guests=2,budget_bytes=64*1024**3,reservation_bytes=40*1024**3,entries=[self.entry])
        self.write_ledger()
        self.python=dict(executable=env.binding(self.token),runtime_dll=None)
        self.handoff=dict(sources=copy.deepcopy(self.sources),helper=env.binding(rules.OPERATOR),python=self.python,
            prepare_proposal=self.prepare_pin,capacity_preview=self.write(self.base/'capacity.json',dict(would_fit=False)),
            artifacts=dict(build=env.binding(self.build_path),product_apk=env.binding(self.product),test_apk=env.binding(self.test)),
            build_copy=env.binding(self.build_copy))
        self.handoff_path=self.base/'handoff.json';self.write(self.handoff_path,self.handoff)
        self.stack.enter_context(patch.object(rules,'HANDOFF',env.binding(self.handoff_path)))
        self.installed=dict(adb=env.binding(self.token),tools=[env.binding(self.token)],python=self.python,auth_key_path=str(self.base/'DO_NOT_READ_KEY'),
            capabilities=env.binding(self.token),source_review=env.binding(self.token),compatibility=env.binding(self.token),emulator=env.binding(self.token),
            qemu=env.binding(self.token),refuser=env.binding(self.token),refuser_source=env.binding(self.token))
        self.authority=dict(version=1,scope='sdk16-fresh-prepare-and-one-knowledge-ui-run-v1',source_head=rules.SOURCE_HEAD,operator_head='a'*40,
            proposal=env.binding(rules.PROPOSAL),operator=env.binding(rules.OPERATOR),contract=env.binding(rules.CONTRACT),handoff=copy.deepcopy(rules.HANDOFF),
            ledger=env.binding(self.registry/'ledger-v1.json'),allow_sdk_prepare=True,allow_one_boot=True,allow_model=False,allow_retirement=False,
            approval_reference='SYNTHETIC FIXTURE ONLY; NEVER HUMAN AUTHORITY',max_operation_seconds=2400)
        self.authority_pin=self.write(rules.AUTHORITY,self.authority)
        self.prepare_authorization=self.write(rules.PREPARE_AUTHORIZATION,dict(version=1,phase='prepare',proposal_sha256=self.prepare_pin['sha256'],allow_environment_calls=True,root_go_pending=False))
        self.inspector=SimpleNamespace(_git=Mock(side_effect=lambda root,head=None:head or 'a'*40),
            validate_handoff=Mock(side_effect=lambda h:copy.deepcopy(h)),_plan=Mock(side_effect=self.check_plan),_capacity=Mock())
        fake_env=SimpleNamespace(**{name:getattr(env,name) for name in ('binding','check_binding','read_json','create_json','safe_path','encoded','decode_json','validate_proposal','verify_prepared','check_authorization')})
        fake_env.verify_installation=Mock(side_effect=lambda p:self.events.append('installation'))
        fake_env.check_external_state=Mock(side_effect=lambda p:self.events.append('external'))
        fake_env.plan_run=Mock(side_effect=self.plan_run)
        fake_env.authorize=Mock(side_effect=self.authorize)
        fake_env.prepare=Mock(side_effect=lambda *args:self.events.append('prepare'))
        self.contract=SimpleNamespace(BOOT_CLAIM_FILE='guest-boot-claim-v1.json',PROTOCOL='owned-emulator-knowledge-ui-v1',
            source_bindings=Mock(side_effect=lambda:copy.deepcopy(self.sources)),validate_admission=Mock(side_effect=self.validate_admission),
            revalidate_inputs=Mock(side_effect=lambda a:self.events.append('revalidate')))
        self.api=SimpleNamespace(env=fake_env,storage=storage,history=history,inspector=self.inspector,contract=self.contract,
            build=SimpleNamespace(verify_frozen_product=Mock(side_effect=lambda artifacts:copy.deepcopy(self.manifest))),
            profile_build=SimpleNamespace(verify_current=Mock(side_effect=lambda a:self.events.append('build'))),
            probe=SimpleNamespace(_python_bindings=Mock(return_value=self.python)),
            base=SimpleNamespace(PROTOCOL='synthetic-private-server',SDK_VERSION=1,SOURCE_NAMES={'core_fixture.py'}),
            activation=SimpleNamespace(HELPER=self.source/'benchmarks/knowledge_ui_activation.py',CONTROL=self.base/'activation-control',
                execute=Mock(return_value=dict(passed=False))))
        self.stack.enter_context(patch.object(bridge,'_parts',return_value=(rules,self.api)))
        # File-only static metadata has its own tests elsewhere. This port is
        # explicit; no frozen external installed path is opened by this fixture.
        self.stack.enter_context(patch.object(bridge,'_installed',return_value=copy.deepcopy(self.installed)))
        return self

    def __exit__(self,*error):
        self.stack.close()  # Restore ports only. Every fixture file is retained.

    def write(self,path,value):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(env.encoded(value));return env.binding(path)

    def write_ledger(self):return self.write(self.registry/'ledger-v1.json',self.ledger)

    def make_proposal(self):
        sdk=self.base/'sdk';java=self.base/'jdk';java.mkdir()
        files=[Path(env.__file__).resolve(),Path(env.host.__file__).resolve(),Path(env.commit_capacity.__file__).resolve(),Path(storage.__file__).resolve(),Path(history.__file__).resolve()]
        for relative in ('platform-tools/adb.exe','emulator/emulator.exe','cmdline-tools/latest/bin/avdmanager.bat','system-images/android-35/google_apis/x86_64/data/empty_data_disk'):
            p=sdk/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'SYNTHETIC SDK NOT EXECUTABLE');files.append(p)
        return dict(version=1,phase='prepare',avd_name=env.NAME,serial='emulator-5592',console_port=5592,sdk=str(sdk),java_home=str(java),
            paths=env.paths(self.guest),adb_path=str(sdk/'platform-tools/adb.exe'),token=env.token_binding(self.token),old_avd={'synthetic':True},
            bindings=[env.binding(p) for p in files],userdata_mib=12288,sdcard_mib=8192,memory_mib=8192,cores=4,
            host_free_min=env.root_free_min(self.guest),host_available_memory_min=12*env.GIB,allow_environment_calls=False,root_go_pending=True)

    def make_prepared_files(self):
        content=Path(self.proposal['paths']['content']);registry=Path(self.proposal['paths']['registry']);content.mkdir(parents=True);registry.mkdir(parents=True)
        immutable=[]
        for p in (content/'config.ini',content/'config.created.ini',registry/(env.NAME+'.ini')):
            p.write_bytes(b'SYNTHETIC immutable config');immutable.append(env.binding(p))
        sd=content/'sdcard.img';sd.write_bytes(b'SYNTHETIC initial tiny disk')
        self.prepared_record=dict(version=1,proposal_sha256=self.prepare_pin['sha256'],avd_name=env.NAME,immutable=immutable,
            initial_sdcard=env.binding(sd),userdata_absent=True,guest_boot_verified=False,facts={})
        self.prepare_result=dict(version=1,proposal_sha256=self.prepare_pin['sha256'],status='completed',closure_verified=True,child_cleanup_complete=True,prepared_created=True)
        self.write(self.guest/'prepared-v1.json',self.prepared_record);self.write(self.guest/'prepare-result-v1.json',self.prepare_result)

    def check_plan(self,proposal):
        env.validate_proposal(proposal,'prepare')
        if (proposal['memory_mib'],proposal['cores'])!=(8192,4):raise env.EnvironmentRefused('fixture_profile')

    def plan_run(self,*args,**kwargs):
        self.events.append('plan_run');return env.plan_run(*args,**kwargs)

    def authorize(self,proposal,authorization,phase):
        self.events.append('authorize');value=env.read_json(proposal);env.validate_proposal(value,phase)
        env.check_authorization(env.read_json(authorization),phase,env.digest(proposal))
        self.api.env.verify_installation(value);self.api.env.check_external_state(value);return value

    def validate_admission(self,value):
        # Explicit SDK16 observation port, not a substitute real contract claim.
        self.events.append('admission')
        if value['protocol']!='owned-emulator-knowledge-ui-v1' or value['guest']['root']!=str(self.guest):raise rules.FreshRunRefused('fixture_admission')
        if (value['guest']['memory_mib'],value['guest']['cores'],value['guest']['api'])!=(8192,4,35):raise rules.FreshRunRefused('fixture_profile')
        for pin in (value['guest']['proposal'],value['guest']['authorization']):env.check_binding(pin)

    def create(self):return bridge.create_inputs(self.authority_pin,self.prepare_authorization)

    def prepared(self):return bridge.prepared(self.authority_pin,self.prepare_authorization)

    def stage_ready(self):
        record=dict(version=1,scope='sdk16-fresh-operation-attempt-v1',authority=self.authority_pin,
            handoff=self.authority['handoff'],operator=self.authority['operator'],contract=self.authority['contract'],no_retry=True)
        self.attempt_pin=self.write(rules.ATTEMPT,record)
        self.write(self.live/'worker-claim-v1.json',dict(version=1,authority=self.authority_pin,attempt=self.attempt_pin))
        return self.attempt_pin
