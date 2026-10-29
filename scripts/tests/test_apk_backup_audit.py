"""Original main-level backup policy fixtures; every aapt process is simulated."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

from scripts.tests import test_audit_apk as fixtures

audit=fixtures.audit
URI='http://schemas.android.com/apk/res/android:'
ATTRS=(('allowBackup','0x01010280','false'),('fullBackupContent','0x010104eb','false'),
       ('dataExtractionRules','0x0101063e','@0x7f0b0000'))
DOMAINS=('root','file','database','sharedpref','external')
OPTIONAL=('device_root','device_file','device_database','device_sharedpref')
RULE_PATH='res/xml/data_extraction_rules.xml'
RESOURCE=('Binary APK\nPackage name=org.locallore.app id=7f\n'
          '  type xml id=0b entryCount=1\n'
          '    resource 0x7f0b0000 xml/data_extraction_rules\n'
          '      () (file) res/xml/data_extraction_rules.xml type=XML\n')


def attribute(name,identifier,value,indent=8,namespace=URI):
    return ' '*indent+'A: '+namespace+name+'('+identifier+')='+value+'\n'


def manifest():
    tree=fixtures.TREE.replace('  E: manifest (line=2)\n',
        'N: android=http://schemas.android.com/apk/res/android (line=2)\n'
        '  E: manifest (line=2)\n'
        '    A: package="org.locallore.app" (Raw: "org.locallore.app")\n')
    return tree+'      E: application (line=17)\n'+''.join(attribute(*item)for item in ATTRS)


def exclusion(domain,path='.'):
    return ('        E: exclude (line=4)\n'
        '          A: domain="'+domain+'" (Raw: "'+domain+'")\n'
        '          A: path="'+path+'" (Raw: "'+path+'")\n')


def section(name,domains=DOMAINS):
    return '    E: '+name+' (line=3)\n'+''.join(exclusion(name)for name in domains)


def rules():return 'E: data-extraction-rules (line=2)\n'+section('cloud-backup')+section('device-transfer')


class ApkBackupAuditTests(unittest.TestCase):
    def setUp(self):
        base=Path(tempfile.mkdtemp(prefix='locallore-backup-audit-',dir='D:/Dev/_Temp'))
        self.assertEqual(base.drive.upper(),'D:');self.apk=base/"hero's backup.apk"
        with zipfile.ZipFile(self.apk,'x')as archive:
            for name in ('AndroidManifest.xml','resources.arsc',RULE_PATH):
                archive.writestr(name,b'original synthetic compiled-resource placeholder')

    def run_main(self,tree=None,resources=None,xml=None,fail=None):
        tree=manifest()if tree is None else tree
        resources=RESOURCE if resources is None else resources
        xml=rules()if xml is None else xml;calls=[];output=io.StringIO()
        def run(argv,**kwargs):
            self.assertIs(kwargs['shell'],False);self.assertIs(kwargs['check'],True)
            self.assertIs(kwargs['capture_output'],True);self.assertEqual(kwargs['encoding'],'utf-8')
            self.assertEqual(argv[:2],[str(Path('D:/Synthetic/aapt2.exe')),'dump']);calls.append(list(argv))
            if argv[2]=='badging':kind,value='badging',fixtures.BADGING
            elif argv[2]=='resources':kind,value='resources',resources
            elif argv[2]=='xmltree':
                file=argv[argv.index('--file')+1]
                kind,value=('manifest',tree)if file=='AndroidManifest.xml'else('rules',xml)
            else:raise AssertionError('unexpected synthetic aapt command')
            if fail==kind:raise subprocess.CalledProcessError(1,argv,output='original capture failure')
            return SimpleNamespace(stdout=value)
        with patch.object(audit,'audit_zip',return_value=[]),patch.object(audit,'aapt2_path',return_value=Path('D:/Synthetic/aapt2.exe')),patch.object(audit.subprocess,'run',side_effect=run),redirect_stdout(output):
            result=audit.main([str(self.apk)])
        return result,output.getvalue(),calls

    def refused(self,**kwargs):self.assertEqual(self.run_main(**kwargs)[0],1)

    def test_current_policy_and_uniform_crlf_are_accepted_with_same_cli_schema(self):
        for crlf,extra in ((False,False),(True,True)):
            xml=rules()if not extra else 'E: data-extraction-rules (line=2)\n'+section('cloud-backup',DOMAINS+OPTIONAL)+section('device-transfer',DOMAINS+OPTIONAL)
            values=(manifest(),RESOURCE+'  type string id=09 entryCount=1\n    resource 0x7f090001 string/unrelated\n      () "café_日本"\n',xml)
            if crlf:values=tuple(value.replace('\n','\r\n')for value in values)
            with self.subTest(crlf=crlf):
                code,text,_=self.run_main(tree=values[0],resources=values[1],xml=values[2])
                self.assertEqual(code,0);self.assertEqual(set(json.loads(text)),{'status','permissions','libraries'})

    def test_backup_flags_are_false_typed_unique_and_application_scoped(self):
        good=manifest()
        for name,identifier,value in ATTRS[:2]:
            line=attribute(name,identifier,value)
            bad=(good.replace(line,''),good.replace(line,attribute(name,identifier,'true')),
                 good.replace(line,attribute(name,identifier,'"false" (Raw: "false")')),
                 good.replace(line,line+line),good.replace(line,attribute(name,'0x0101ffff','false')),
                 good.replace(line,attribute(name,identifier,'false',namespace='wrong:')),
                 good.replace(line,'          E: activity (line=18)\n'+attribute(name,identifier,'false',12)))
            for index,tree in enumerate(bad):
                with self.subTest(flag=name,variant=index):self.refused(tree=tree)

    def test_rules_reference_and_manifest_ownership_cannot_be_missing_or_ambiguous(self):
        good=manifest();line=attribute(*ATTRS[2]);package='    A: package="org.locallore.app" (Raw: "org.locallore.app")\n'
        variants=(good.replace(line,''),good.replace(line,line+line),good.replace(line,attribute('dataExtractionRules','0x0101063e','@0x7f0b0001')),
                  good.replace(line,attribute('dataExtractionRules','0x0101ffff','@0x7f0b0000')),
                  good.replace(line,'          E: activity (line=18)\n'+attribute(*ATTRS[2],indent=12)),
                  good.replace(package,''),good.replace(package,package+package),good.replace(package,package.replace('org.locallore.app','org.foreign.app')),
                  good+'      E: application (line=99)\n'+''.join(attribute(*item)for item in ATTRS),good+good)
        for index,tree in enumerate(variants):
            with self.subTest(variant=index):self.refused(tree=tree)

    def test_resource_must_resolve_once_to_own_default_xml_without_alias_or_variant(self):
        entry='    resource 0x7f0b0000 xml/data_extraction_rules\n      () (file) '+RULE_PATH+' type=XML\n'
        variants=('',RESOURCE.replace(entry,''),RESOURCE+entry,RESOURCE.replace('name=org.locallore.app','name=org.foreign.app'),
                  RESOURCE.replace('0x7f0b0000','0x800b0000'),RESOURCE.replace('      () (file) '+RULE_PATH+' type=XML','      () @0x7f0b0001'),
                  RESOURCE.replace('      () (file)','      (night) (file)'),RESOURCE+'      (v31) (file) '+RULE_PATH+' type=XML\n',
                  RESOURCE.replace(RULE_PATH,'res/xml/../xml/data_extraction_rules.xml'),RESOURCE.replace(' type=XML',' type=STRING'))
        for index,resources in enumerate(variants):
            with self.subTest(variant=index):self.refused(resources=resources)

    def test_both_sections_are_required_unique_and_have_no_unknown_attributes(self):
        good=rules()
        for name in ('cloud-backup','device-transfer'):
            block=section(name)
            for index,xml in enumerate((good.replace(block,''),good+block,good.replace(block,block.replace('    E: '+name,'    E: unknown-section')),
                good.replace('    E: '+name+' (line=3)\n','    E: '+name+' (line=3)\n      A: disableIfNoEncryptionCapabilities=true\n'))):
                with self.subTest(section=name,variant=index):self.refused(xml=xml)

    def test_each_mandatory_domain_is_full_root_unique_and_not_replaced_by_optional_domains(self):
        for name in ('cloud-backup','device-transfer'):
            block=section(name)
            for domain in DOMAINS:
                line=exclusion(domain)
                variants=(block.replace(line,''),block.replace(line,exclusion(domain,'private/')),
                          block.replace(line,line+line),block.replace(line,''.join(exclusion(item)for item in OPTIONAL)))
                for index,changed in enumerate(variants):
                    with self.subTest(section=name,domain=domain,variant=index):self.refused(xml=rules().replace(block,changed))

    def test_permissive_or_malformed_exclusion_nodes_are_refused(self):
        good=rules();line=exclusion('root')
        variants=(good.replace('E: exclude','E: include',1),good.replace(line,line+'          A: extra="private"\n',1),
                  good.replace('A: path="." (Raw: ".")\n','A: path="." (Raw: ".")\n          A: path="." (Raw: ".")\n',1),
                  good.replace(line,exclusion('unknown-domain'),1),good.replace(line,line+'            E: exclude (line=9)\n',1),
                  good+good,good.replace('E: data-extraction-rules','E: wrong-root',1))
        for index,xml in enumerate(variants):
            with self.subTest(variant=index):self.refused(xml=xml)

    def test_resource_and_rules_capture_failures_and_malformed_framing_fail_closed(self):
        for kind in ('resources','rules'):
            with self.subTest(capture=kind):self.refused(fail=kind)
        for kind,value in (('resources',RESOURCE.replace('\n','\r\n',1)),('xml',rules()+'\x00'),('resources',b'not decoded text')):
            with self.subTest(framing=kind):self.refused(**{kind:value})


if __name__=='__main__':unittest.main()
