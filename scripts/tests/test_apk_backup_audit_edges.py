"""Additional main-level backup boundaries; no imported TestCase duplication."""
import unittest

from scripts.tests import test_apk_backup_audit as fixtures


class ApkBackupAuditEdgeTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.ApkBackupAuditTests(methodName='runTest')
        self.fixture.setUp()

    def result(self,**kwargs):return self.fixture.run_main(**kwargs)
    def refused(self,**kwargs):self.assertEqual(self.result(**kwargs)[0],1)

    def test_application_overrides_and_aliased_critical_framework_ids_are_refused(self):
        good=fixtures.manifest()
        for name,identifier in (('backupAgent','0x0101027f'),('defaultToDeviceProtectedStorage','0x01010504')):
            for label in (name,'innocentAttribute'):
                for value in ('false','true','"org.original.CustomAgent" (Raw: "org.original.CustomAgent")'):
                    with self.subTest(policy=name,label=label,value=value):
                        self.refused(tree=good+fixtures.attribute(label,identifier,value))
        for name,identifier,_ in fixtures.ATTRS:
            with self.subTest(duplicate_id=name):
                self.refused(tree=good+fixtures.attribute('unrelatedAttribute',identifier,'true'))

    def test_resource_type_package_count_and_entry_index_join_the_reference(self):
        # A nonzero entry index is valid when both reference and table agree and
        # the type's entry range includes it; counts are not resource identities.
        tree=fixtures.manifest().replace('@0x7f0b0000','@0x7f0b0001')
        resources=fixtures.RESOURCE.replace('entryCount=1','entryCount=2').replace('0x7f0b0000','0x7f0b0001')
        self.assertEqual(self.result(tree=tree,resources=resources)[0],0)
        variants=(resources.replace('entryCount=2','entryCount=1'),resources.replace('id=0b','id=0c'),
                  resources.replace('type xml','type string'),resources.replace('entryCount=2','entryCount=0'),
                  resources.replace('entryCount=2','entryCount=65537'),resources.replace('entryCount=2','entryCount=02'),
                  resources.replace('id=7f','id=80'),resources+'Package name=org.foreign id=80\n')
        for index,value in enumerate(variants):
            with self.subTest(variant=index):self.refused(tree=tree,resources=value)

    def test_namespace_ownership_and_misleading_raw_strings_cannot_supply_authority(self):
        good=fixtures.manifest();namespace=good.splitlines(keepends=True)[0]
        variants=(namespace+good,namespace.replace('android=http','android=https')+good,
                  good+'          E: activity (line=99)\n'+fixtures.attribute(*fixtures.ATTRS[0]),
                  good.replace('package="org.locallore.app" (Raw: "org.locallore.app")',
                               'package="org.locallore.app" (Raw: "org.foreign.app")'))
        for index,tree in enumerate(variants):
            with self.subTest(manifest=index):self.refused(tree=tree)
        for index,xml in enumerate((fixtures.rules().replace('domain="root" (Raw: "root")','domain="root" (Raw: "file")',1),
                                   fixtures.rules().replace('path="." (Raw: ".")','path="." (Raw: "private/")',1),
                                   fixtures.rules()+'N: extra=http://example.invalid (line=99)\n')):
            with self.subTest(rules=index):self.refused(xml=xml)

    def test_metadata_bounds_are_enforced_on_otherwise_unrelated_manifest_and_resource_data(self):
        good=fixtures.manifest();node_count=sum(line.lstrip().startswith('E: ')for line in good.splitlines())
        at_nodes=good+'          E: meta-data (line=99)\n'*(4096-node_count)
        self.assertEqual(self.result(tree=at_nodes)[0],0)
        code,text,_=self.result(tree=at_nodes+'          E: meta-data (line=99)\n')
        self.assertEqual(code,1);self.assertIn('bounds',text)
        attrs=sum(line.lstrip().startswith('A: ')for line in good.splitlines())
        at_attrs=good+''.join('        A: unrelated%d="x"\n'%index for index in range(16384-attrs))
        self.assertEqual(self.result(tree=at_attrs)[0],0)
        code,text,_=self.result(tree=at_attrs+'        A: oneMore="x"\n')
        self.assertEqual(code,1);self.assertIn('Too many backup attributes',text)
        deep='E: data-extraction-rules (line=2)\n'+''.join(' '*(4*depth)+'E: layer (line=3)\n'for depth in range(1,33))
        code,text,_=self.result(xml=deep);self.assertEqual(code,1);self.assertIn('depth',text)
        at_lines=fixtures.RESOURCE+'\n'*(65536-len(fixtures.RESOURCE.splitlines()))
        self.assertEqual(len(at_lines.splitlines()),65536)
        self.assertEqual(self.result(resources=at_lines)[0],0)
        self.refused(resources=at_lines+'\n')
        extra=('  type string id=09 entryCount=1\n'
               '    resource 0x7f090001 string/unrelated\n'
               '      () "')
        suffix='"\n';prefix=fixtures.RESOURCE+extra
        at_size=prefix+'x'*(4*1024*1024-len(prefix)-len(suffix))+suffix
        self.assertEqual(len(at_size),4*1024*1024)
        self.assertEqual(self.result(resources=at_size)[0],0)
        self.refused(resources=at_size+' ')


if __name__=='__main__':unittest.main()
