"""Original tiny SDK15 byte graphs, not synthetic Android/XML/DEX qualification.

Only fixed baseline/Git authority is coherently substituted. Every referenced
payload and alias is an actual isolated D: file; no verdict function is mocked.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
from benchmarks import library_ui_build as b

HOME=Path('D:/Dev/Experiments/LocalLore/2026-11-02-library-ui-harness-v1/build-agent-v1/fixtures')
def encoded(v):return json.dumps(v,sort_keys=True).encode()
def pin(p):
 raw=p.read_bytes();return dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def put(p,raw):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(raw)
 return pin(p)


class Graph:
 def __init__(self,product_permissions=None):
  HOME.mkdir(parents=True,exist_ok=True);self.home=Path(tempfile.mkdtemp(prefix='library-',dir=HOME))
  self.root,self.out,self.rec,self.native_out=(self.home/n for n in ('product','capture','recovery','native'))
  self.fixed=copy.deepcopy(b._FIXED);self.fixed.update(root=str(self.root),capture=str(self.out),recovery=str(self.rec),native_capture=str(self.native_out),manifest=str(self.home/'manifest.json'))
  self.source={};self.r={};self.refs={};self.baseline=self.home/'baseline.json'
  production=['apps/android/app/src/main/java/org/locallore/app/'+n for n in ('ShellViewModel.kt','MainActivity.kt','ui/LocalLoreScreen.kt')]
  for name in ['crates/synthetic/lib.rs',b.ORACLE,b.UI_SOURCE]+production+b.DOC_DELTA:
   self.source[name]=put(self.root/name,('opaque current '+name).encode())
  self.oracle_sha=self.source[b.ORACLE]['sha256']
  self.fixed.update(first_count=len(self.source)-2,tested_count=len(self.source)-1,source_count=len(self.source),native_source_count=len(self.source)-2)
  def rows(first=False,unavailable=False):
   result=[]
   for name,p in self.source.items():
    if name==b.DOC_DELTA[1] or first and name==b.UI_SOURCE:continue
    raw=(b'prior documentation' if name==b.DOC_DELTA[0] else b'unavailable Espresso source' if unavailable and name==b.UI_SOURCE else (self.root/name).read_bytes())
    result.append(dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
   return result
  with patch.object(b,'_FIXED',self.fixed):self.paths=b._paths()
  for key,path in self.paths.items():
   if b._binary(key):self.refs[key]=put(path,('opaque reviewed '+key).encode())
  for role,p in self.fixed['apks'].items():
   self.fixed['apks'][role]=put(self.root/('apps/android/app/build/outputs/apk/debug/app-debug.apk' if role=='product_apk' else 'apps/android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk'),('opaque '+role).encode())
  old_apk=put(self.home/'old-recovery/inherited-test.apk',b'inherited old unqualified test')
  old_source=dict(old_apk,path=str(self.root/'old-original-test.apk'))
  fresh_source=put(self.out/'inherited-original.txt',b'old XML byte record')
  fresh_copy=put(self.rec/'inherited-build-v1/old.xml',Path(fresh_source['path']).read_bytes())
  inherited=[dict(source=old_source,copy=old_apk,reused_immutable_copy=True),dict(source=fresh_source,copy=fresh_copy)]
  self.fixed.update(inherited_count=2,reused_count=1,new_inherited_count=1,inherited_bytes=old_apk['bytes']+fresh_copy['bytes'],new_inherited_bytes=fresh_copy['bytes'])
  self.r['inherited']=dict(files=inherited,total_bytes=self.fixed['inherited_bytes'],new_copy_bytes=fresh_copy['bytes'])
  case_names=['case'+str(i) for i in range(12)]
  for name,head,total,failures,code,elapsed in b._PHASES:
   self.r[name+'/before']=dict(head=head,files=rows(first=name=='first-v1',unavailable=name in ('green-v2','android-v1')))
   self.r[name+'/after']=copy.deepcopy(self.r[name+'/before'])
   full=name.startswith('android-');partial=name=='android-v1'
   worker=dict(pid=12,creation_filetime=102,executable='C:/Synthetic/python.exe')
   command=([worker['executable'],'-I','-S','-B','scripts/check.py','android','--offline'] if full else [str(self.root/'apps/android/gradlew.bat'),'-p','apps/android','--offline','--no-daemon','--max-workers=2',':app:testDebugUnitTest','--tests','org.locallore.app.LibraryActionScopeShellTest'])
   raw='> Task :app:buildRustAndroid UP-TO-DATE\n'
   if partial:raw+=':app:compileDebugAndroidTestKotlin FAILED\n'
   elif name=='android-v2':
    raw+='BUILD SUCCESSFUL\n81 actionable tasks: 8 executed, 73 up-to-date\n'
    raw+=json.dumps(dict(status='passed',permissions=(b._PRODUCT_PERMISSIONS[:] if product_permissions is None else product_permissions),libraries=[{}]*4))+'\n'
    raw+=json.dumps(dict(status='passed',certificate_sha256=self.fixed['certificate'],package='org.locallore.app',test_package='org.locallore.app.test',test_permissions=['android.permission.REORDER_TASKS'],app={k:self.fixed['apks']['product_apk'][k] for k in ('bytes','sha256')},test={k:self.fixed['apks']['test_apk'][k] for k in ('bytes','sha256')}))+'\n'
   stdout=self.paths[name+'/stdout'];stdout.write_bytes(raw.encode());self.refs[name+'/stdout']=pin(stdout)
   stderr=self.paths[name+'/stderr'];stderr.write_bytes(b"Unresolved reference 'Espresso'\nUnresolved reference 'pressBack'" if partial else b'');self.refs[name+'/stderr']=pin(stderr)
   owner=dict(status='child_exited',worker_returncode=code,elapsed_ms=elapsed,cleanup_complete=True,output_capture_complete=True,stdout_bytes=self.refs[name+'/stdout']['bytes'],stderr_bytes=self.refs[name+'/stderr']['bytes'])
   self.r[name+'/owner']=owner;self.r[name+'/terminal']=dict(owner=owner,passed=code==0,source_equal=True,faults=[])
   self.r[name+'/request']=dict(head=head,cwd=str(self.root),seconds=900,helper={k:self.refs['helper'][k] for k in ('bytes','sha256')},owner=dict(worker,pid=11,creation_filetime=101),command=command,source_archive=self.refs['zip/'+head])
   self.r[name+'/actual_child']=dict(identity=worker,helper=self.r[name+'/request']['helper'])
   self.r[name+'/command_child']=dict(identity=dict(worker,pid=13,creation_filetime=103,executable=worker['executable'] if full else 'C:/Windows/System32/cmd.exe'),command=command)
   self.r[name+'/command_terminal']=dict(returncode=code)
   pairs=[]
   for index in range(67 if full else 1):
    original=self.root/'apps/android/app/build/test-results/testDebugUnitTest'/('TEST-'+str(index)+'.xml')
    original.parent.mkdir(parents=True,exist_ok=True);original.write_bytes(('opaque report '+name+str(index)).encode())
    copy_path=self.out/name/('partial-reports-v1' if partial else 'reports')/original.name
    pairs.append(dict(source=pin(original),copy=put(copy_path,original.read_bytes())))
   cases=[dict(suite='org.locallore.app.LibraryActionScopeShellTest',name=n,failure=['java.lang.AssertionError'] if i<failures else [],errors=0,skipped=0) for i,n in enumerate(case_names)]
   cases += [dict(suite='Synthetic.Recorded',name='old'+str(i),failure=[],errors=0,skipped=0) for i in range(total-12)]
   record=dict(files=pairs,cases=cases,tests=total,unique=total,failures=failures,errors=0,skipped=0)
   if partial:
    record=dict(jvm_xml=pairs,tests=total,failures=0,errors=0,skipped=0,overall_passed=False)
    record['failed_current_product']=dict(source=self.fixed['apks']['product_apk'],copy=put(self.rec/'failed-build-v1/app-debug.apk',Path(self.fixed['apks']['product_apk']['path']).read_bytes()))
    record['inherited_test_apk']=dict(source=old_source,copy=old_apk)
   if name=='android-v2':
    for role,p in self.fixed['apks'].items():
     filename='outputs__apk__debug__app-debug.apk' if role=='product_apk' else 'outputs__apk__androidTest__debug__app-debug-androidTest.apk'
     record['files'].append(dict(source=p,copy=put(self.rec/'current-build-v1'/filename,Path(p['path']).read_bytes())))
   self.r[name+'/reports']=record
  self.r['final_source']=dict(head=self.fixed['head'],files=[dict(path=name,bytes=p['bytes'],sha256=p['sha256']) for name,p in self.source.items()])
  self.r['source_review_prior']=dict(result='no-concrete-source-blocker-found')
  self.record('source_review_prior')
  self.r['source_review']=dict(result='no-concrete-source-blocker-found',previous_review=self.refs['source_review_prior'],production_comparison=[dict(p,matches_prior=True) for n,p in self.source.items() if n in production])
  self.r['closed']=dict(ui_executed=False,lint_severities={'Hint':1,'Warning':1},failed_full_gate=dict(overall_passed=False,old_test_apk_unqualified=True,final_product_audits_not_run=True),compiled_only_ui_methods=[dict(method=row[2],runtime_junit=True,code_units=5) for row in b.ROSTER])
  self.r['review']=dict(result='verified-no-evidence-mismatch',findings=[],ui_execution=False,failed_full_gate_preserved=True,source_archives_replayed=4,all_four_wrappers_delegate_to_helper=True,compiled_journey_code_units=40)
  pairs=[]
  for index in range(3):
   original=put(self.out/f'controls/{index}.bin',b'control '+bytes([index]));preserved=put(self.rec/f'controls-v1/controls/{index}.bin',Path(original['path']).read_bytes());pairs.append(dict(source=original,copy=preserved))
  for name in b.DOC_DELTA:pairs.append(dict(source=self.source[name],copy=put(self.rec/'final-source-overlay-v1'/name,(self.root/name).read_bytes())))
  self.fixed['preservation_pairs']=len(pairs)
  self.r['preservation']=dict(head=self.fixed['head'],tested_head=self.fixed['tested_head'],sources=len(self.source),overlay_paths=b.DOC_DELTA,files=pairs,no_full_generated_tree_backup=True)
  self.record('preservation');put(self.rec/'final-preservation-v1.json',self.paths['preservation'].read_bytes())
  self.r['preservation_review']=dict(result='verified-no-mismatch',findings=[],head=self.fixed['head'],reconstructed_source_files=len(self.source),manifest=self.refs['preservation'])
  self.r['native/before']=dict(head=self.fixed['native_compiled_head'],files=rows(first=True));self.r['native/after']=copy.deepcopy(self.r['native/before'])
  self.r['native/owner']=dict(status='child_exited',worker_returncode=1,cleanup_complete=True,output_capture_complete=True)
  self.r['native/terminal']=dict(owner=self.r['native/owner'],source_equal=True,passed=False,faults=[])
  self.r['native/request']=dict(recorded=True)
  native_stdout=self.paths['native/stdout'];native_stdout.write_bytes(b'Building LocalLore Rust JNI: x86_64-linux-android\nBuilding LocalLore Rust JNI: aarch64-linux-android\n');self.refs['native/stdout']=pin(native_stdout)
  self.native=[];build=self.root/'apps/android/app/build'
  lint=put(build/'reports/lint-results-debug.xml',b'opaque recorded lint, not XML qualification')
  self.r['android-v2/reports']['files'].append(dict(source=lint,copy=put(self.rec/'current-build-v1/reports__lint-results-debug.xml',Path(lint['path']).read_bytes())))
  for target,abi in [('x86_64-linux-android','x86_64'),('aarch64-linux-android','arm64-v8a')]:
   release=build/f'rust-target/{target}/release/liblocallore_android.so';put(release,('native '+abi).encode());alias=release.parent/'deps/liblocallore_android.so';alias.parent.mkdir();os.link(release,alias)
   row=dict(abi=abi,release=pin(release),cargo_alias=pin(alias),release_alias_links=2)
   for key,p in [('generated',f'generated/rustJniLibs/{abi}/liblocallore_android.so'),('merged',f'intermediates/merged_native_libs/debug/mergeDebugNativeLibs/out/lib/{abi}/liblocallore_android.so'),('stripped',f'intermediates/stripped_native_libs/debug/stripDebugDebugSymbols/out/lib/{abi}/liblocallore_android.so')]:row[key]=put(build/p,('stripped '+abi).encode() if key=='stripped' else release.read_bytes())
   row['apk_sha256']=row['stripped']['sha256'];self.native.append(row)
   self.r['android-v2/reports']['files'].append(dict(source=row['generated'],copy=put(self.rec/'current-build-v1'/('generated__rustJniLibs__'+abi+'__liblocallore_android.so'),Path(row['generated']['path']).read_bytes())))
  for key in self.paths:
   if not b._binary(key) and key not in self.refs:self.record(key)
  self.r['android-v1/reports']['phase_terminal']=self.refs['android-v1/terminal'];self.paths['android-v1/reports'].write_bytes(encoded(self.r['android-v1/reports']));self.refs['android-v1/reports']=pin(self.paths['android-v1/reports'])
  self.value=dict(version=1,scope=b.MODE,product=self.fixed,refs=self.refs,roster=b.ROSTER,facts=b._FACTS,native=self.native,documentation_only_delta=b.DOC_DELTA,source_encoding=b.SOURCE_ENCODING)
  self.seal()
 def record(self,key):self.refs[key]=put(self.paths[key],encoded(self.r[key]))
 def seal(self):self.baseline.write_bytes(encoded(self.value));self.baseline_pin=pin(self.baseline)
 def git(self,args):
  if args==['rev-parse','HEAD']:return (self.fixed['head']+'\n').encode()
  if args[0]=='status':return b''
  if args==['ls-files','-z']:return ('\0'.join(self.source)+'\0').encode()
  raise AssertionError('unexpected Git observation')
 def patches(self):return patch.multiple(b,_FIXED=self.fixed,BASELINE_PATH=self.baseline,BASELINE_BYTES=self.baseline_pin['bytes'],BASELINE_SHA256=self.baseline_pin['sha256'],ORACLE_SHA256=self.oracle_sha,_git=self.git)


@unittest.skipUnless(os.name=='nt','D-only held-stream byte fixtures')
class LibraryBuildTests(unittest.TestCase):
 def setUp(self):
  self.g=Graph();self.stack=ExitStack();self.addCleanup(self.stack.close);self.stack.enter_context(self.g.patches())
  for target in ('socket.socket','socket.create_connection','subprocess.run','subprocess.Popen'):self.stack.enter_context(patch(target,side_effect=AssertionError('external operation')))
 def test_original_positive_graph_returns_four_scoped_roles_without_publishing(self):
  result=b.create_manifest();self.assertEqual(result['roster'],b.ROSTER);self.assertEqual(len(result['roster']),4)
  self.assertEqual(result['validation_mode'],b.MODE);self.assertFalse(Path(self.g.fixed['manifest']).exists())
  self.assertFalse(result['recorded_execution']['facts']['android_runtime_executed'])
  result['roster'][0][0]='changed';self.assertEqual(b.create_manifest()['roster'],b.ROSTER)
 def test_product_permission_is_exact_and_missing_extra_or_network_permissions_refuse(self):
  expected=['org.locallore.app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION']
  self.assertEqual(b._PRODUCT_PERMISSIONS,expected)
  for permissions in ([],expected+['android.permission.READ_CONTACTS'],expected+['android.permission.INTERNET'],['android.permission.INTERNET']):
   graph=Graph(product_permissions=permissions)
   with self.subTest(permissions=permissions),graph.patches(),self.assertRaisesRegex(b.BuildRefused,'^audit$'):
    b.create_manifest()
 def test_fixed_manifest_copy_mode_extra_roles_and_swapped_apks_refuse(self):
  path=Path(self.g.fixed['manifest']);put(path,encoded(b.create_manifest()));roles=dict(build=pin(path),**self.g.fixed['apks'])
  self.assertEqual(b.verify_frozen_product(roles)['roster'],b.ROSTER)
  for kind in ('path','scope','mode','extra','swap'):
   changed=copy.deepcopy(roles)
   if kind=='path':changed['build']['path']=str(self.g.home/'copy.json')
   elif kind=='extra':changed['model']=changed['build']
   elif kind=='swap':changed['product_apk'],changed['test_apk']=changed['test_apk'],changed['product_apk']
   else:
    value=b.create_manifest();value['scope' if kind=='scope' else 'validation_mode']='sdk14';path.write_bytes(encoded(value));changed['build']=pin(path)
   with self.subTest(kind=kind),self.assertRaises(b.BuildRefused):b.verify_frozen_product(changed)
 def test_source_evidence_apk_and_preserved_copy_tampering_refuse(self):
  paths=[self.g.root/'crates/synthetic/lib.rs',self.g.paths['green-v3/owner'],self.g.paths['android-v1/reports'],Path(self.g.fixed['apks']['test_apk']['path']),Path(self.g.r['preservation']['files'][0]['copy']['path'])]
  for path in paths:
   original=path.read_bytes();path.write_bytes(original+b'changed')
   with self.subTest(path=str(path)),self.assertRaises(b.BuildRefused):b.create_manifest()
   path.write_bytes(original)
 def test_owner_identity_cleanup_command_and_integer_boolean_fences(self):
  for kind in ('identity','cleanup','command','bool'):
   record=copy.deepcopy(self.g.r)
   if kind=='identity':record['green-v3/command_child']['identity']=record['green-v3/actual_child']['identity']
   elif kind=='cleanup':record['green-v3/owner']['cleanup_complete']=False
   elif kind=='command':record['green-v3/command_child']['command'][-1]='foreign'
   else:record['android-v1/command_terminal']['returncode']=True
   with self.subTest(kind=kind),self.assertRaises(b.BuildRefused):b._execution(b._Reader(),self.g.value,record)
 def test_failed_partial_gate_cannot_be_promoted_or_old_apk_qualified(self):
  for kind in ('passed','old','audit'):
   record=copy.deepcopy(self.g.r)
   if kind=='passed':record['android-v1/reports']['overall_passed']=True
   elif kind=='old':record['closed']['failed_full_gate']['old_test_apk_unqualified']=False
   else:record['closed']['failed_full_gate']['final_product_audits_not_run']=False
   with self.subTest(kind=kind),self.assertRaises(b.BuildRefused):b._execution(b._Reader(),self.g.value,record)
 def test_roster_body_flags_and_review_cannot_be_name_only(self):
  for key,value in [('runtime_junit',False),('code_units',True),('code_units',0),('code_units',8193)]:
   record=copy.deepcopy(self.g.r);record['closed']['compiled_only_ui_methods'][0][key]=value
   with self.subTest(key=key,value=value),self.assertRaises(b.BuildRefused):b._execution(b._Reader(),self.g.value,record)
 def test_source_head_cleanliness_roster_and_baseline_location_are_fixed(self):
  real=self.g.git
  for kind in ('head','dirty','roster'):
   def observed(args):
    if kind=='head' and args[0]=='rev-parse':return b'0'*40+b'\n'
    if kind=='dirty' and args[0]=='status':return b' M src/file\n'
    if kind=='roster' and args[0]=='ls-files':return b'foreign\0'
    return real(args)
   with self.subTest(kind=kind),patch.object(b,'_git',side_effect=observed),self.assertRaises(b.BuildRefused):b.create_manifest()
  self.assertEqual(str(b.create_manifest()['baseline']['path']),str(self.g.baseline))
 def test_duplicate_json_nonfinite_bad_version_and_size_are_rejected(self):
  for raw in (b'{"version":1,"version":1}',b'{"number":NaN}',b'{"number":Infinity}'):
   with self.subTest(raw=raw),self.assertRaises((b.BuildRefused,ValueError)):b._json(raw)
  with self.assertRaises(b.BuildRefused):b._binding(dict(path=str(self.g.baseline),bytes=True,sha256='0'*64))
  with self.assertRaises(b.BuildRefused):b._binding(dict(path=str(self.g.baseline),bytes=64*1024**2+1,sha256='0'*64))
 def test_held_stream_late_change_deadline_total_budget_and_hardlink_refuse(self):
  path=self.g.root/'crates/synthetic/lib.rs';reader=b._Reader();reader.read(pin(path));original=path.read_bytes();path.write_bytes(original+b'late')
  with self.assertRaises(b.BuildRefused):reader.final()
  path.write_bytes(original);reader=b._Reader();reader.until=0
  with self.assertRaises(b.BuildRefused):reader.read(pin(path))
  reader=b._Reader();reader.total=512*1024**2
  with self.assertRaises(b.BuildRefused):reader.read(pin(path))
  os.link(path,self.g.home/'unexpected-hardlink')
  with self.assertRaises(b.BuildRefused):b._Reader().read(pin(path))
 def test_manifest_and_import_do_not_publish_or_perform_target_io(self):
  source=Path(b.__file__).read_bytes()
  with patch('builtins.open',side_effect=AssertionError('import file IO')),patch.object(Path,'open',side_effect=AssertionError('import path IO')):
   value={'__file__':b.__file__,'__name__':'isolated_import'};exec(compile(source,b.__file__,'exec'),value)
  self.assertTrue(callable(value['verify_current']));self.assertFalse(Path(self.g.fixed['manifest']).exists())
 def test_lazy_current_contract_revalidates_around_real_byte_validation(self):
  path=Path(self.g.fixed['manifest']);put(path,encoded(b.create_manifest()));value=dict(artifacts=dict(build=pin(path),**self.g.fixed['apks']))
  module=types.ModuleType('benchmarks.owned_library_ui_contract');calls=[]
  module.validate_admission=lambda v:(calls.append('validate') or copy.deepcopy(v))
  module.revalidate_inputs=lambda v:calls.append('revalidate')
  with patch.dict('sys.modules',{'benchmarks.owned_library_ui_contract':module}),patch.object(__import__('benchmarks'),'owned_library_ui_contract',module,create=True):
   self.assertEqual(b.verify_current(value)['roster'],b.ROSTER)
  self.assertEqual(calls,['validate','revalidate','revalidate'])


if __name__=='__main__':unittest.main()
