"""Original external-restart byte-proof adversaries; no process or model calls.

Synthetic consistency is not execution authentication or proof of Android death.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from benchmarks import original_author_restart_proof as r
from scripts.tests import test_original_author_prompt_provenance as provenance

f=provenance.f
CURRENT='initial-world-v1.1'
LEGACY='initial-world-v1'
RECORDS=('workspace-before-v1.json','recover-v1.json','snapshot-v1.json','retry-v1.json','workspace-after-v1.json','archive-v1.json')


class RestartFixture:
    def __init__(self,version=CURRENT):
        baseline=provenance.fixture(version)
        self.author=baseline['author'];self.author_artifacts=baseline['artifacts'];self.import_raw=baseline['imported']
        created=json.loads(self.author_artifacts['create-v1.json'])['data']
        recover=dict(session='restart-session-1',scope=copy.deepcopy(created['scope']),revision=0,created=False)
        self.artifacts={'workspace-before-v1.json':self.author_artifacts['workspace-created-v1.json'],
          'recover-v1.json':f.raw(f.reply(recover)),'snapshot-v1.json':self.author_artifacts['snapshot-created-v1.json'],
          'retry-v1.json':f.raw(f.reply(dict(recover,session='restart-session-2'))),
          'workspace-after-v1.json':self.author_artifacts['workspace-created-v1.json'],'archive-v1.json':self.author_artifacts['archive-v1.json']}
        self.proof=dict(version=1,scope='original_author_external_restart_v1',status='completed',stage='completed',reason=None,
          process=dict(pid=503,uid=10421,start_elapsed_ms=30000),package=f.p.PACKAGE,elapsed_ms=300,
          import_proof_sha256=f.sha(self.import_raw),author_proof_sha256=f.sha(self.author_raw),
          records={name:f.binding(self.artifacts[name])for name in RECORDS},pending_before=False,pending_after=False,
          workspace_closed=True,archive_closed=True)

    @property
    def author_raw(self):return f.raw(self.author)

    def validate(self,**kwargs):
        return r.validate_restart(f.raw(self.proof),self.artifacts,self.author_raw,self.author_artifacts,self.import_raw,**kwargs)

    def replace(self,name,mutate):
        value=json.loads(self.artifacts[name]);mutate(value);self.artifacts[name]=f.raw(value)
        self.proof['records'][name]=f.binding(self.artifacts[name])

    def rebind_baseline(self,name,mutate):
        f.replace_artifact(self.author,self.author_artifacts,name,mutate)
        self.proof['author_proof_sha256']=f.sha(self.author_raw)


class OriginalAuthorRestartProofTests(unittest.TestCase):
    def refused(self,call):
        with self.assertRaises(r.RestartRefused)as caught:call()
        self.assertNotIn('SYNTHETIC_PRIVATE_CANARY',str(caught.exception))

    def test_original_complete_external_restart_copies_and_performs_no_file_io(self):
        v=RestartFixture();before=copy.deepcopy((v.proof,v.artifacts,v.author,v.author_artifacts,v.import_raw))
        with patch.object(Path,'open',side_effect=AssertionError('file open')),patch.object(Path,'stat',side_effect=AssertionError('file stat')):
            result=v.validate()
        self.assertEqual(result,v.proof);result['process']['pid']=999;result['records']['recover-v1.json']['bytes']=1
        self.assertEqual((v.proof,v.artifacts,v.author,v.author_artifacts,v.import_raw),before)

    def test_same_numeric_pid_is_permitted_only_with_newer_start_and_same_uid(self):
        v=RestartFixture();v.proof['process']['pid']=v.author['process']['pid'];self.assertEqual(v.validate(),v.proof)
        for field,bad in(('pid',0),('pid',True),('uid',9999),('uid',10422),('uid',True),
                         ('start_elapsed_ms',8000),('start_elapsed_ms',7999),('start_elapsed_ms',True)):
            v=RestartFixture();v.proof['process'][field]=bad
            with self.subTest(field=field,bad=bad):self.refused(v.validate)

    def test_internal_host_reopen_is_not_external_restart_authority(self):
        v=RestartFixture();v.proof['process']=copy.deepcopy(v.author['process']);self.refused(v.validate)
        v=RestartFixture();v.proof['scope']='original_author_model_v1';self.refused(v.validate)
        v=RestartFixture();v.artifacts['snapshot-reopened-v1.json']=v.author_artifacts['snapshot-reopened-v1.json'];self.refused(v.validate)

    def test_exact_top_level_schema_complete_stage_and_package(self):
        for key,bad in(('version',True),('version',2),('scope','original_author_external_restart_v2'),('package','foreign.package'),
                         ('status','refused'),('stage','snapshot'),('reason','checks_failed'),('elapsed_ms',True),
                         ('elapsed_ms',-1),('elapsed_ms',180001),('source_model_accessed',False),('author_requested',True),
                         ('private_rows','SYNTHETIC_PRIVATE_CANARY')):
            v=RestartFixture();v.proof[key]=bad
            with self.subTest(key=key):self.refused(v.validate)
        for key in tuple(RestartFixture().proof):
            v=RestartFixture();v.proof.pop(key)
            with self.subTest(missing=key):self.refused(v.validate)

    def test_complete_requires_observed_false_pending_and_true_checked_closure(self):
        for field in('pending_before','pending_after','workspace_closed','archive_closed'):
            for bad in(None,0,1,'false',field.startswith('pending')):
                v=RestartFixture();v.proof[field]=bad
                with self.subTest(field=field,bad=bad):self.refused(v.validate)

    def test_refused_or_unknown_observations_never_become_completed(self):
        for stage in('admission','open','recover','snapshot','retry','archive','close'):
            v=RestartFixture();v.proof.update(status='refused',stage=stage,reason='resource_uncertain',pending_before=None,
              pending_after=None,workspace_closed=None,archive_closed=None)
            with self.subTest(stage=stage):self.refused(v.validate)

    def test_restart_process_closed_fields_cannot_hide_runtime_or_uid_claims(self):
        for key,bad in(('uid',10422),('extra','SYNTHETIC_PRIVATE_CANARY'),('start_elapsed_ms',None)):
            v=RestartFixture();v.proof['process'][key]=bad;self.refused(v.validate)

    def test_exact_import_and_author_raw_hashes_are_bound(self):
        for key in('import_proof_sha256','author_proof_sha256'):
            for bad in('0'*64,'A'*64,True,None):
                v=RestartFixture();v.proof[key]=bad
                with self.subTest(key=key,bad=bad):self.refused(v.validate)
        v=RestartFixture();v.import_raw+=b' ';self.refused(v.validate)
        v=RestartFixture();v.author['elapsed_ms']+=1;self.refused(v.validate)

    def test_original_author_and_import_must_validate_before_recovery(self):
        for field,bad in(('status','refused'),('stage','create'),('review_sha256','0'*64)):
            v=RestartFixture();v.author[field]=bad;v.proof['author_proof_sha256']=f.sha(v.author_raw);self.refused(v.validate)
        v=RestartFixture();imported=json.loads(v.import_raw);imported['source_counts']['closed']=0
        v.import_raw=f.raw(imported);v.author['prior_import_sha256']=f.sha(v.import_raw)
        v.proof.update(import_proof_sha256=f.sha(v.import_raw),author_proof_sha256=f.sha(v.author_raw));self.refused(v.validate)

    def test_baseline_second_model_attempt_or_changed_provenance_does_not_recover(self):
        v=RestartFixture();v.rebind_baseline('worker-v2.json',lambda value:value.update(creations_total=2));self.refused(v.validate)
        v=RestartFixture();v.rebind_baseline('archive-v1.json',lambda value:value['payload']['story']['seed']['initial_world']['generation'].update(provider='scripted'))
        self.refused(v.validate)

    def test_record_and_artifact_rosters_are_exact_and_complete(self):
        for name in RECORDS:
            for kind in('missing_artifact','missing_record','null'):
                v=RestartFixture()
                if kind=='missing_artifact':v.artifacts.pop(name)
                elif kind=='missing_record':v.proof['records'].pop(name)
                else:v.proof['records'][name]=None
                with self.subTest(name=name,kind=kind):self.refused(v.validate)
        v=RestartFixture();v.artifacts['model.task']=b'not a model';self.refused(v.validate)
        v=RestartFixture();v.proof['records']['unexpected.json']=f.binding(b'{}');self.refused(v.validate)

    def test_all_exact_record_bytes_and_binding_types_are_checked(self):
        for name in RECORDS:
            v=RestartFixture();v.artifacts[name]+=b' '
            with self.subTest(name=name):self.refused(v.validate)
        for key,bad in(('bytes',True),('bytes',0),('bytes',-1),('sha256','0'*64),('sha256','A'*64),('path','private path')):
            v=RestartFixture();v.proof['records']['recover-v1.json'][key]=bad
            with self.subTest(key=key):self.refused(v.validate)
        v=RestartFixture();v.artifacts['recover-v1.json']=bytearray(v.artifacts['recover-v1.json']);self.refused(v.validate)

    def test_strict_json_utf8_unique_keys_finite_scalars_and_proof_cap(self):
        v=RestartFixture()
        for raw in(b'',b'\xff',b'{} trailing',b'{"version":1,"version":1}',b'{"x":NaN}',b'{"x":Infinity}',b'{"x":1e999}',
                   b'{"x":"\\ud800"}',b' '*(32768+1)):
            with self.subTest(raw=raw[:25]):
                self.refused(lambda:r.validate_restart(raw,v.artifacts,v.author_raw,v.author_artifacts,v.import_raw))

    def test_record_json_is_strict_even_when_byte_binding_is_recomputed(self):
        for raw in(b'\xff',b'{"version":1,"version":1}',b'{"x":NaN}',b'{} trailing',b'{"x":"\\ud800"}'):
            v=RestartFixture();v.artifacts['recover-v1.json']=raw;v.proof['records']['recover-v1.json']=f.binding(raw)
            with self.subTest(raw=raw[:20]):self.refused(v.validate)

    def test_individual_and_aggregate_record_caps_are_enforced(self):
        v=RestartFixture();v.artifacts['recover-v1.json']=b' '*(1024*1024+1);v.proof['records']['recover-v1.json']=f.binding(v.artifacts['recover-v1.json']);self.refused(v.validate)
        v=RestartFixture()
        for name in RECORDS:
            v.artifacts[name]+=b' '*400000;v.proof['records'][name]=f.binding(v.artifacts[name])
        self.refused(v.validate)

    def test_original_native_envelopes_reject_extra_keys_or_bool_versions(self):
        for name in RECORDS[:-1]:
            for key,bad in(('version',True),('status','rejected'),('extra','SYNTHETIC_PRIVATE_CANARY')):
                v=RestartFixture();v.replace(name,lambda value:value.__setitem__(key,bad))
                with self.subTest(name=name,key=key):self.refused(v.validate)

    def test_recover_and_retry_require_original_scope_created_false_revision_zero(self):
        for name in('recover-v1.json','retry-v1.json'):
            for key,bad in(('created',True),('created',0),('revision',1),('revision',False),('session',1),('session',True),
                             ('session',''),('session','bad session'),('scope',dict(story='foreign',branch='main'))):
                v=RestartFixture();v.replace(name,lambda value:value['data'].__setitem__(key,bad))
                with self.subTest(name=name,key=key):self.refused(v.validate)

    def test_catalog_preserves_all_stories_scope_title_revision_and_drafts(self):
        for name in('workspace-before-v1.json','workspace-after-v1.json'):
            for change in(lambda data:data['stories'].clear(),lambda data:data['stories'].append(copy.deepcopy(data['stories'][0])),
                          lambda data:data['stories'][0].update(title='Changed'),lambda data:data['stories'][0].update(revision=1),
                          lambda data:data['stories'][0].update(drafts=1),lambda data:data.update(persistent=False)):
                v=RestartFixture();v.replace(name,lambda value:change(value['data']))
                with self.subTest(name=name):self.refused(v.validate)

    def test_snapshot_preserves_player_lens_truth_inventory_and_receipts(self):
        for change in(lambda data:data['player'].update(observer='npc'),lambda data:data['player'].update(facts=[dict(text='private fact')]),
                      lambda data:data['player'].update(observations=[dict(text='invented discovery')]),lambda data:data.update(inventory={'forged':1}),
                      lambda data:data.update(receipts=[dict(id='forged')]),lambda data:data.update(rules='tactical_v1'),
                      lambda data:data['scope'].update(branch='foreign'),lambda data:data.update(revision=1)):
            v=RestartFixture();v.replace('snapshot-v1.json',lambda value:change(value['data']));self.refused(v.validate)

    def test_archive_is_exact_original_bytes_not_semantic_reencoding_or_repair(self):
        v=RestartFixture();v.artifacts['archive-v1.json']+=b' ';v.proof['records']['archive-v1.json']=f.binding(v.artifacts['archive-v1.json']);self.refused(v.validate)
        v=RestartFixture();v.replace('archive-v1.json',lambda value:value['payload']['branches'][0].update(head_revision=1));self.refused(v.validate)

    def test_current_default_and_explicit_legacy_prompt_selection_do_not_relabel_origin(self):
        v=RestartFixture(LEGACY);self.refused(v.validate)
        self.assertEqual(v.validate(expected_prompt_version=LEGACY),v.proof)
        v=RestartFixture();self.refused(lambda:v.validate(expected_prompt_version=LEGACY))
        for selector in(True,None,1,{},[],'initial-world-v2'):
            with self.subTest(selector=selector):self.refused(lambda:v.validate(expected_prompt_version=selector))


if __name__=='__main__':unittest.main()
