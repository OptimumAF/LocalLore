"""Physical caller must bind strict backup policy to the selected compiled resource.

Synthetic D APKs and tool captures only; backup and manifest validators are real.
"""
import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import zipfile

from scripts.tests import test_audit_physical_model_apk as legacy

p=legacy.p
URI='http://schemas.android.com/apk/res/android:'
RULE='res/xml/data_extraction_rules.xml'
FLAGS=(('allowBackup','0x01010280','false'),('fullBackupContent','0x010104eb','false'),
       ('debuggable','0x0101000f','true'),('dataExtractionRules','0x0101063e','@0x7f0b0000'))


def attr(name,identity,value,indent=8):
    rendered=value if value in ('true','false','0x2')or value.startswith('@')else '"'+value+'" (Raw: "'+value+'")'
    return ' '*indent+'A: '+URI+name+'('+identity+')='+rendered+'\n'


def manifests(fixture=False):
    permission=p.APP+'.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'
    badging="package: name='%s' versionCode='1'\nminSdkVersion:'26'\ntargetSdkVersion:'36'\nuses-permission: name='%s'\nlaunchable-activity: name='org.locallore.app.LocalModelSetupActivity'\n"%(p.APP,permission)
    root='N: android=http://schemas.android.com/apk/res/android (line=2)\n  E: manifest (line=2)\n'
    app=root+'    A: package="'+p.APP+'" (Raw: "'+p.APP+'")\n'
    app+='      E: permission (line=11)\n'+attr('name','0x01010003',permission)+attr('protectionLevel','0x01010009','0x2')
    app+='      E: application (line=17)\n'+''.join(attr(*row)for row in FLAGS)
    activities=[('LocalModelSetupActivity','true'),('LiteRtPlayActivity','false'),('MainActivity','false')]
    if fixture:activities.append((p.SETUP_FIXTURE,'false'))
    for name,exported in activities:
        app+='          E: activity (line=28)\n'+attr('name','0x01010003','org.locallore.app.'+name,12)+attr('exported','0x01010010',exported,12)
        if name in ('LocalModelSetupActivity','LiteRtPlayActivity'):app+=attr('launchMode','0x0101001d','0x2',12)
        if name=='LocalModelSetupActivity':app+='              E: intent-filter (line=30)\n                  E: category (line=31)\n'+attr('name','0x01010003','android.intent.category.LAUNCHER',20)
    test_badging="package: name='%s' versionCode='1'\nminSdkVersion:'26'\ntargetSdkVersion:'36'\nuses-permission: name='android.permission.REORDER_TASKS'\n"%p.TEST
    test=root+'    A: package="'+p.TEST+'" (Raw: "'+p.TEST+'")\n'
    test+='      E: instrumentation (line=3)\n'+attr('name','0x01010003',p.RUNNER)+attr('targetPackage','0x01010021',p.APP)
    test+='      E: application (line=5)\n'+attr('debuggable','0x0101000f','true')
    for name,suffix,process in (('ChooserArchiveProvider$Control','chooser.control',':chooser_test_provider'),('ChooserArchiveProvider','chooser',':chooser_test_provider'),('ArchiveDocumentProvider','archives',':archive_test_provider'),('TestDiagnosticProvider','diagnostics',':diagnostic_test_provider')):
        test+='          E: provider (line=6)\n'+attr('name','0x01010003','org.locallore.app.'+name,12)+attr('authorities','0x01010018',p.TEST+'.'+suffix,12)+attr('process','0x01010011',process,12)+attr('exported','0x01010010','true',12)
        if name=='ChooserArchiveProvider':test+=attr('permission','0x01010006','android.permission.MANAGE_DOCUMENTS',12)+attr('grantUriPermissions','0x0101001b','true',12)
    rules='E: data-extraction-rules (line=2)\n'
    for name in ('cloud-backup','device-transfer'):
        rules+='    E: '+name+' (line=3)\n'
        for domain in ('root','file','database','sharedpref','external'):
            rules+='        E: exclude (line=4)\n          A: domain="'+domain+'" (Raw: "'+domain+'")\n          A: path="." (Raw: ".")\n'
    resources='Binary APK\nPackage name='+p.APP+' id=7f\n  type xml id=0b entryCount=1\n    resource 0x7f0b0000 xml/data_extraction_rules\n      () (file) '+RULE+' type=XML\n'
    return [badging,app,test_badging,test,rules,resources]


class PhysicalBackupLinkageTests(unittest.TestCase):
    def setUp(self):
        base=Path(tempfile.mkdtemp(prefix='locallore-physical-backup-',dir='D:/Dev/_Temp'))
        self.assertEqual(base.drive.upper(),'D:');self.app=base/'synthetic-app.apk';self.test=base/'synthetic-tests.apk'
        for file in (self.app,self.test):
            with zipfile.ZipFile(file,'x')as archive:archive.writestr('AndroidManifest.xml',b'original compiled-manifest placeholder')

    def call(self,metadata=None,*,fixture=False,flag=False,main=True,fail=None):
        values=manifests(fixture)if metadata is None else metadata
        app_classes,test_classes=legacy.classes()
        if fixture:app_classes[p.descriptor(p.SETUP_FIXTURE)]=(17,[])
        calls=[];signer=Mock(return_value='d'*64);output=io.StringIO()
        def tool(command):
            args=[str(item)for item in command];calls.append(args)
            self.assertEqual(args[:2],[str(Path('D:/Synthetic/aapt2.exe')),'dump'])
            app=str(self.app)in args
            if args[2]=='badging':kind,value='badging',values[0 if app else 2]
            elif args[2]=='resources':kind,value='resources',values[5]
            elif args[2]=='xmltree':
                file=args[args.index('--file')+1]
                kind,value=('manifest',values[1 if app else 3])if file=='AndroidManifest.xml'else('rules',values[4])
            else:raise AssertionError('unexpected synthetic tool operation')
            if fail==kind:raise p.AuditError('original capture refusal')
            return value
        def classes(path):return copy.deepcopy(app_classes if Path(path)==self.app else test_classes)
        with patch.object(p.base,'audit_zip',return_value=[]),patch.object(p,'dex_classes',side_effect=classes),patch.object(p.base,'aapt2_path',return_value=Path('D:/Synthetic/aapt2.exe')),patch.object(p,'tool',side_effect=tool),patch.object(p,'certificate',signer),redirect_stdout(output):
            if main:
                args=['--app',str(self.app),'--test',str(self.test)]+(['--physical-setup-fixture']if flag else[])
                result=p.main(args)
            else:result=p.audit_pair(self.app,self.test,physical_fixture=flag)
        return result,output.getvalue(),calls,signer

    def refused(self,metadata,*,before_rules=False):
        code,text,calls,signer=self.call(metadata)
        self.assertEqual(code,1);self.assertEqual(json.loads(text)['status'],'failed');self.assertNotIn('"passed"',text)
        signer.assert_not_called()
        if before_rules:self.assertFalse(any('--file'in row and row[row.index('--file')+1]!= 'AndroidManifest.xml'for row in calls))

    def test_canonical_physical_profiles_require_the_existing_explicit_fixture_optin(self):
        for fixture,flag in ((False,False),(True,True)):
            with self.subTest(fixture=fixture):
                code,text,_,signer=self.call(fixture=fixture,flag=flag)
                self.assertEqual(code,0);self.assertEqual(json.loads(text)['status'],'passed');self.assertEqual(signer.call_count,2)
                value,_,_,_=self.call(fixture=fixture,flag=flag,main=False)
                self.assertEqual(set(value),{'version','scope','status','app','test','signer_sha256','methods','manifest','libraries'})
        for fixture,flag in ((True,False),(False,True)):
            code,text,_,signer=self.call(fixture=fixture,flag=flag)
            self.assertEqual(code,1);self.assertEqual(json.loads(text)['status'],'failed');signer.assert_not_called()

    def test_resource_reference_table_alias_and_variant_fail_before_rules_or_signing(self):
        good=manifests();variants=[]
        for reference in ('@0x7f0b0001','@0x7f090000','@xml/unrelated'):
            value=copy.deepcopy(good);value[1]=value[1].replace('@0x7f0b0000',reference);variants.append(value)
        for table in ('',good[5].replace('      () (file) '+RULE+' type=XML','      () @0x7f0b0001'),
                      good[5].replace('() (file)','(night) (file)'),good[5].replace('Package name='+p.APP,'Package name=org.foreign.app'),good[5].replace('id=0b','id=0c')):
            value=copy.deepcopy(good);value[5]=table;variants.append(value)
        for index,value in enumerate(variants):
            with self.subTest(variant=index):self.refused(value,before_rules=True)

    def test_typed_framework_flags_namespaces_and_override_ids_use_strict_backup_parser(self):
        good=manifests();tree=good[1];line=attr(*FLAGS[0])
        app_marker='      E: application (line=17)\n'
        variants=(tree.replace(line,line.replace('=false','=\"false\" (Raw: \"false\")')),
                  tree.replace(URI+'fullBackupContent','wrong:fullBackupContent'),
                  tree.replace('dataExtractionRules(0x0101063e)','dataExtractionRules(0x0101ffff)'),
                  tree.replace(app_marker,app_marker+attr('innocentAttribute','0x0101027f','false')),
                  tree.replace(app_marker,app_marker+attr('defaultToDeviceProtectedStorage','0x01010504','false')),
                  tree.replace(line,line.replace('=false','=true')))
        for index,changed in enumerate(variants):
            value=copy.deepcopy(good);value[1]=changed
            with self.subTest(variant=index):self.refused(value)

    def test_rules_root_sections_nesting_and_raw_values_cannot_bypass_selected_resource(self):
        good=manifests();xml=good[4]
        variants=(xml.replace('E: data-extraction-rules','E: unrelated'),xml+'    E: unreviewed-section (line=90)\n',
                  xml.replace('          A: path="." (Raw: ".")\n','          A: path="." (Raw: ".")\n            E: hidden-child (line=91)\n',1),
                  xml.replace('domain="root" (Raw: "root")','domain="root" (Raw: "file")',1))
        for index,changed in enumerate(variants):
            value=copy.deepcopy(good);value[4]=changed
            with self.subTest(variant=index):self.refused(value)

    def test_resources_capture_is_required_and_success_json_cannot_follow_its_failure(self):
        code,text,_,signer=self.call(fail='resources')
        self.assertEqual(code,1);self.assertEqual(json.loads(text)['status'],'failed');signer.assert_not_called()

    def test_public_pair_does_not_accept_an_arbitrary_reference_to_hardcoded_good_rules(self):
        value=manifests();value[1]=value[1].replace('@0x7f0b0000','@0x7f0b9999')
        with self.assertRaises(p.AuditError):self.call(value,main=False)


if __name__=='__main__':unittest.main()
