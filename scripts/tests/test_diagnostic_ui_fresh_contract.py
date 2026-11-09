"""Original SDK17 structural authority/handoff oracles; no runtime authority.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import ExitStack
import copy
import ctypes
from pathlib import Path, PureWindowsPath
import socket
import subprocess
import unittest
from unittest.mock import patch

from scripts import diagnostic_ui_fresh_contract as rules
from scripts import run_diagnostic_ui_fresh as bridge
from scripts.tests.diagnostic_ui_fresh_input_fixture import SOURCE_NAMES


def pin(path):
    return dict(path=str(PureWindowsPath(path)),bytes=17,sha256='7'*64)


def authority():
    return dict(version=1,scope='sdk17-fresh-prepare-and-one-diagnostic-ui-run-v1',source_head=rules.SOURCE_HEAD,
        proposal=pin(rules.PROPOSAL),operator=pin(rules.OPERATOR),contract=pin(rules.CONTRACT),handoff=copy.deepcopy(rules.HANDOFF),
        ledger=pin(rules.REGISTRY/'ledger-v1.json'),allow_sdk_prepare=True,allow_one_boot=True,allow_model=False,
        allow_retirement=False,approval_reference='SYNTHETIC TEST ONLY; NOT HUMAN AUTHORITY',max_operation_seconds=2400)


def handoff():
    sources=sorted([pin(rules.SOURCE/'benchmarks'/name) for name in SOURCE_NAMES],key=lambda p:p['path'])
    return dict(version=1,scope='sdk17-fresh-inputs-v1',source_root=str(rules.SOURCE),source_head=rules.SOURCE_HEAD,
        source_tree=rules.SOURCE_TREE,guest=str(rules.GUEST),controls=str(rules.CONTROLS),runtime=str(rules.RUNTIME),sources=sources,
        python=dict(executable=pin('C:/Synthetic/python.exe'),runtime_dll=pin('C:/Synthetic/python314.dll')),
        artifacts=dict(build=copy.deepcopy(rules.BUILD_PIN),product_apk=pin('D:/Synthetic/product.apk'),test_apk=pin('D:/Synthetic/test.apk')),
        prepare_proposal=copy.deepcopy(rules.PREPARE_PIN),capacity_preview=pin(rules.READY/'capacity-preview-v1.json'),
        profile=copy.deepcopy(rules.PROFILE),execution_authorized=False,model_material=False)


def attempt(a,p):
    return dict(version=1,scope='sdk17-fresh-operation-attempt-v1',authority=copy.deepcopy(p),handoff=copy.deepcopy(a['handoff']),
        operator=copy.deepcopy(a['operator']),contract=copy.deepcopy(a['contract']),no_retry=True)


def no_io(stack):
    for name in ('open','resolve','stat','lstat','mkdir','unlink','rename','replace'):
        stack.enter_context(patch.object(Path,name,side_effect=AssertionError('unexpected filesystem operation')))
    stack.enter_context(patch.object(ctypes,'WinDLL',create=True,side_effect=AssertionError('unexpected native operation')))
    stack.enter_context(patch.object(subprocess,'Popen',side_effect=AssertionError('unexpected process')))
    stack.enter_context(patch.object(socket,'socket',side_effect=AssertionError('unexpected socket')))


class DiagnosticFreshContractTests(unittest.TestCase):
    def test_import_bodies_and_valid_metadata_need_no_io_and_return_detached_copies(self):
        bodies=[(Path(m.__file__).read_bytes(),m.__name__) for m in (rules,bridge)]
        a=authority();h=handoff();p=pin(rules.AUTHORITY);t=attempt(a,p)
        with ExitStack() as stack:
            no_io(stack)
            for raw,name in bodies:
                ns=dict(__name__=name+'__import_oracle',__file__='D:/Synthetic/scripts/module.py')
                exec(compile(raw,ns['__file__'],'exec'),ns)
            aa=rules.validate_authority(a);hh=rules.validate_handoff(h);tt=rules.validate_attempt(t,p,a)
        self.assertEqual((aa,hh,tt),(a,h,t))
        aa['operator']['sha256']='0'*64;hh['sources'][0]['sha256']='0'*64;tt['authority']['sha256']='0'*64
        self.assertEqual(a['operator']['sha256'],'7'*64)
        self.assertEqual(h['sources'][0]['sha256'],'7'*64)
        self.assertEqual(p['sha256'],'7'*64)
        self.assertFalse(hh['execution_authorized']);self.assertFalse(hh['model_material'])

    def test_authority_rejects_retirement_model_old_sdk_and_noncanonical_grant_types(self):
        cases=[]
        for key,values in (
            ('version',(True,2,'1')),('scope',('sdk16-fresh-prepare-and-one-knowledge-ui-run-v1',)),
            ('source_head',('0'*40,)),('allow_sdk_prepare',(1,False)),('allow_one_boot',(1,False)),
            ('allow_model',(0,True)),('allow_retirement',(0,True)),('max_operation_seconds',(True,2400.0,2401)),
            ('approval_reference',('','private\nline','x'*257))):
            for value in values:
                bad=authority();bad[key]=value;cases.append((key,bad))
        for key in ('operator_head','unknown'):
            bad=authority();bad[key]='a'*40;cases.append((key,bad))
        bad=authority();del bad['allow_model'];cases.append(('missing',bad))
        for name in ('proposal','operator','contract','handoff','ledger'):
            bad=authority();bad[name]['path']=pin('D:/Synthetic/borrowed.json')['path'];cases.append((name,bad))
        bad=authority();bad['handoff']['sha256']='0'*64;cases.append(('stale_handoff',bad))
        for label,bad in cases:
            with self.subTest(label=label),ExitStack() as stack:
                no_io(stack)
                with self.assertRaises(rules.FreshRunRefused):rules.validate_authority(bad)

    def test_binding_strict_types_paths_limits_and_installed_c_python_exception(self):
        original=pin('D:/Synthetic/file.json')
        rules.binding(original)
        rules.binding(pin('C:/Synthetic/python.exe'),maximum=128*1024**2,project=False)
        cases=[]
        for key,values in (('bytes',(True,0,-1,2*1024**2+1,17.0)),('sha256',('A'*64,'0'*63)),
            ('path',('C:\\Synthetic\\file.json','D:/Synthetic/file.json','relative.json','D:\\Synthetic\\private\nfile.json'))):
            for value in values:
                bad=copy.deepcopy(original);bad[key]=value;cases.append((key,bad))
        bad=copy.deepcopy(original);bad['extra']=None;cases.append(('extra',bad))
        for label,bad in cases:
            with self.subTest(label=label),self.assertRaises(rules.FreshRunRefused):rules.binding(bad)
        with self.assertRaises(rules.FreshRunRefused):rules.binding(original,'D:/Synthetic/other.json')

    def test_handoff_profile_roles_and_namespaces_cannot_be_retagged(self):
        cases=[]
        for key,values in (('version',(True,2)),('scope',('sdk16-fresh-inputs-v1',)),('source_head',('0'*40,)),
            ('source_tree',('0'*40,)),('source_root',('D:\\Synthetic\\foreign-source',)),('guest',('D:\\Synthetic\\old-guest',)),
            ('runtime',('D:\\Synthetic\\other-runtime',)),('controls',('D:\\Synthetic\\other-controls',)),
            ('execution_authorized',(0,True)),('model_material',(0,True))):
            for value in values:
                bad=handoff();bad[key]=value;cases.append((key,bad))
        for key,value in (('memory_mib',True),('cores',8),('api',34),('max_run_seconds',1801)):
            bad=handoff();bad['profile'][key]=value;cases.append((key,bad))
        for role in ('build','prepare_proposal'):
            bad=handoff();target=bad['artifacts']['build'] if role=='build' else bad['prepare_proposal']
            target['sha256']='0'*64;cases.append((role,bad))
        bad=handoff();bad['capacity_preview']['path']=pin('D:/Synthetic/unrelated-capacity.json')['path'];cases.append(('capacity',bad))
        bad=handoff();bad['unknown']=False;cases.append(('extra',bad))
        bad=handoff();del bad['python']['runtime_dll'];cases.append(('python-shape',bad))
        for label,bad in cases:
            with self.subTest(label=label),self.assertRaises(rules.FreshRunRefused):rules.validate_handoff(bad)

    def test_handoff_source_roster_shape_rejects_missing_duplicate_unsorted_and_foreign_parent(self):
        cases=[]
        bad=handoff();bad['sources'].pop();cases.append(('missing',bad))
        bad=handoff();bad['sources'].append(copy.deepcopy(bad['sources'][0]));cases.append(('extra',bad))
        bad=handoff();bad['sources'][1]=copy.deepcopy(bad['sources'][0]);cases.append(('duplicate',bad))
        bad=handoff();bad['sources'].reverse();cases.append(('unsorted',bad))
        bad=handoff();bad['sources'][0]['path']=pin('D:/Synthetic/foreign/owned_target_contract.py')['path'];cases.append(('foreign',bad))
        bad=handoff();bad['sources']=tuple(bad['sources']);cases.append(('tuple',bad))
        for label,bad in cases:
            with self.subTest(label=label),self.assertRaises(rules.FreshRunRefused):rules.validate_handoff(bad)
        # Exact basename/hash membership is a live frozen_inputs join, not an
        # invented structural-validator claim. Its tests use the actual builder.
        self.assertEqual(len(rules.validate_handoff(handoff())['sources']),27)

    def test_attempt_binds_exact_authority_roles_and_one_shot_boolean(self):
        a=authority();p=pin(rules.AUTHORITY)
        for role in ('authority','handoff','operator','contract'):
            bad=attempt(a,p);bad[role]['sha256']='0'*64
            with self.subTest(role=role),self.assertRaises(rules.FreshRunRefused):rules.validate_attempt(bad,p,a)
        for key,value in (('version',True),('scope','sdk16-fresh-operation-attempt-v1'),('no_retry',1),('no_retry',False),('extra',None)):
            bad=attempt(a,p);bad[key]=value
            with self.subTest(field=key),self.assertRaises(rules.FreshRunRefused):rules.validate_attempt(bad,p,a)
        wrong=pin('D:/Synthetic/copied-authority.json')
        with self.assertRaises(rules.FreshRunRefused):rules.validate_attempt(attempt(a,wrong),wrong,a)
