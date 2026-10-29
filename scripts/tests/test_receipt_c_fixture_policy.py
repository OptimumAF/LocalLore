"""Original lexical-C fixtures with physical D storage; no real C fixture IO."""
import hashlib
import os
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from benchmarks import receipt_avd_environment as env
from scripts.tests.receipt_c_fixture import SyntheticCVolume


METHODS=('open','mkdir','exists','is_dir','is_file','is_symlink','stat','lstat','iterdir','resolve')


@unittest.skipUnless(os.name=='nt','lexical Windows drive fixtures with physical D backing')
class SyntheticCFixturePolicyTests(unittest.TestCase):
    def setUp(self):
        self.base=Path(tempfile.mkdtemp(prefix='locallore-c-fixture-policy-',dir='D:/Dev/_Temp')).resolve(strict=True)
        self.backing=self.base/'volume';self.backing.mkdir()
        self.original={name:getattr(Path,name)for name in METHODS}
    def restored(self):
        for name,method in self.original.items():self.assertIs(getattr(Path,name),method,name)
    def metadata(self,path,*,mode,attributes):
        original_stat=os.stat;original_lstat=os.lstat;target=Path(path)
        info=original_lstat(target)
        fields={name:getattr(info,name)for name in dir(info)if name.startswith('st_')}
        fields.update(st_mode=mode,st_file_attributes=attributes);synthetic=SimpleNamespace(**fields)
        def inspect(value,*args,**kwargs):
            if isinstance(value,(str,bytes,os.PathLike))and Path(value)==target:return synthetic
            return original_stat(value,*args,**kwargs)
        def inspect_no_follow(value,*args,**kwargs):
            if isinstance(value,(str,bytes,os.PathLike))and Path(value)==target:return synthetic
            return original_lstat(value,*args,**kwargs)
        return patch.multiple(os,stat=inspect,lstat=inspect_no_follow)

    def test_lexical_C_identity_maps_only_to_physical_D_and_keeps_real_floor_rules(self):
        volume=SyntheticCVolume(self.backing);root=volume.root;physical=volume.physical(root)
        self.assertEqual(root.drive.upper(),'C:');self.assertTrue(root.is_absolute())
        self.assertEqual(root.parent.parent,Path('C:/__locallore_test__'))
        self.assertEqual(physical,self.backing/'new-avd');self.assertEqual(physical.drive.upper(),'D:')
        with volume:
            self.assertFalse(root.exists());self.assertFalse(physical.exists())
            self.assertEqual(env.root_free_min(root),{'C:':40*env.GIB,'D:':40*env.GIB})
            self.assertEqual(env.root_free_min(physical),{'C:':16*env.GIB,'D:':40*env.GIB})
            self.assertEqual(env.safe_path(root,exists=False),root)
        self.restored();self.assertEqual(volume.physical(root),physical)

    def test_path_mkdir_binary_and_text_io_are_real_D_bytes_with_lexical_C_results(self):
        volume=SyntheticCVolume(self.backing);raw=b'original synthetic fixture\0\x1a\xff\r\n'
        with volume:
            root=volume.root;root.mkdir();nested=root/'nested';nested.mkdir();file=nested/'binary.bin'
            self.assertEqual(file.write_bytes(raw),len(raw));self.assertEqual(file.read_bytes(),raw)
            text=root/'text.txt';text.write_text('original fixture\n',encoding='utf-8');self.assertEqual(text.read_text(encoding='utf-8'),'original fixture\n')
            with(root/'open.bin').open('wb')as stream:stream.write(raw)
            self.assertEqual((root/'open.bin').read_bytes(),raw)
            self.assertEqual(file.stat().st_size,len(raw));self.assertEqual(file.lstat().st_size,len(raw))
            self.assertTrue(file.is_file());self.assertFalse(file.is_dir());self.assertTrue(nested.is_dir());self.assertFalse(file.is_symlink())
            self.assertEqual(file.resolve(),file);self.assertEqual(env.digest(file),hashlib.sha256(raw).hexdigest())
        self.assertEqual(volume.physical(file).read_bytes(),raw);self.restored()

    def test_iterdir_returns_only_lexical_C_children_and_actual_D_roster_matches(self):
        volume=SyntheticCVolume(self.backing)
        with volume:
            root=volume.root;root.mkdir();(root/'first.txt').write_text('first');(root/'second').mkdir()
            children=set(root.iterdir());self.assertEqual(children,{root/'first.txt',root/'second'})
            self.assertTrue(all(child.drive.upper()=='C:'for child in children))
            self.assertEqual({p.name for p in volume.physical(root).iterdir()},{'first.txt','second'})
        self.restored()

    def test_pure_mapping_rejects_traversal_prefix_collision_foreign_C_and_relative_names(self):
        volume=SyntheticCVolume(self.backing);root=volume.root;anchor=root.parent
        candidates=(root/'..'/'escape',root/'nested'/'..'/'escape',Path(str(anchor)+'-collision')/'new-avd',
                    Path('C:/__locallore_test__/unmapped-volume/new-avd'),Path('relative'),Path('C:relative'))
        for path in candidates:
            with self.subTest(path=str(path)),self.assertRaises(ValueError):volume.physical(path)
        self.assertEqual(list(self.backing.iterdir()),[]);self.restored()

    def test_foreign_C_reads_writes_directory_and_metadata_calls_refuse_before_IO(self):
        volume=SyntheticCVolume(self.backing);foreign=Path('C:/__locallore_test__/unmapped-volume/new-avd')
        calls=(lambda:foreign.open('wb'),lambda:foreign.write_bytes(b'never written'),lambda:foreign.read_bytes(),
               lambda:foreign.mkdir(parents=True),lambda:list(foreign.iterdir()),lambda:foreign.stat(),
               lambda:foreign.lstat(),lambda:foreign.resolve(),lambda:foreign.exists())
        with volume:
            for number,call in enumerate(calls):
                with self.subTest(operation=number),self.assertRaises(ValueError):call()
        self.assertEqual(list(self.backing.iterdir()),[]);self.restored()

    def test_traversal_filesystem_calls_cannot_escape_the_assigned_D_backing(self):
        volume=SyntheticCVolume(self.backing);escaped=volume.root/'..'/'..'/'escaped.txt'
        with volume:
            for call in(lambda:escaped.write_bytes(b'never written'),lambda:escaped.mkdir(parents=True),lambda:escaped.stat()):
                with self.assertRaises(ValueError):call()
        self.assertFalse((self.base/'escaped.txt').exists());self.assertEqual(list(self.backing.iterdir()),[])

    def test_exception_restores_all_patch_scopes_without_removing_fixture_bytes(self):
        volume=SyntheticCVolume(self.backing);error=KeyboardInterrupt()
        try:
            with volume:volume.root.mkdir();(volume.root/'kept.bin').write_bytes(b'kept');raise error
        except BaseException as observed:self.assertIs(observed,error)
        else:self.fail('fixture scope suppressed original exception')
        self.restored();self.assertEqual((self.backing/'new-avd/kept.bin').read_bytes(),b'kept')

    def test_two_active_volumes_remain_isolated_and_inner_exception_does_not_drop_outer_scope(self):
        second=self.base/'second';second.mkdir();one=SyntheticCVolume(self.backing);two=SyntheticCVolume(second)
        self.assertNotEqual(one.root,two.root)
        with one:
            one.root.mkdir();(one.root/'one.txt').write_text('one')
            try:
                with two:
                    two.root.mkdir();(two.root/'two.txt').write_text('two')
                    self.assertEqual((one.root/'one.txt').read_text(),'one');self.assertEqual((two.root/'two.txt').read_text(),'two')
                    raise LookupError('original nested fixture exception')
            except LookupError:pass
            self.assertEqual((one.root/'one.txt').read_text(),'one');self.assertFalse((one.root/'two.txt').exists())
        self.restored();self.assertEqual((self.backing/'new-avd/one.txt').read_text(),'one');self.assertEqual((second/'new-avd/two.txt').read_text(),'two')

    def test_normal_D_operations_are_not_redirected_while_a_C_volume_is_active(self):
        volume=SyntheticCVolume(self.backing);file=self.base/'normal-D.txt'
        with volume:file.write_text('normal D bytes');self.assertEqual(file.read_text(),'normal D bytes');self.assertEqual(file.resolve(),file)
        self.assertTrue(file.is_file());self.assertEqual(list(self.backing.iterdir()),[]);self.restored()

    def test_backing_must_be_physical_D_directory_before_any_patch_is_installed(self):
        file=self.base/'not-a-directory';file.write_bytes(b'preserve')
        for backing in(Path('relative'),Path('C:/__locallore_test__/not-a-backing'),file):
            with self.subTest(backing=str(backing)),self.assertRaises(ValueError):
                with SyntheticCVolume(backing):self.fail('invalid backing entered')
            self.restored()
        self.assertEqual(file.read_bytes(),b'preserve')

    def test_symlink_or_reparse_backing_metadata_refuses_without_real_link_creation(self):
        for mode,attributes in((stat.S_IFLNK|0o777,0),(stat.S_IFDIR|0o700,0x400)):
            with self.subTest(mode=mode,attributes=attributes),self.metadata(self.backing,mode=mode,attributes=attributes):
                with self.assertRaises(ValueError):
                    with SyntheticCVolume(self.backing):self.fail('unsafe backing entered')
            self.restored()

    def test_backing_reparse_appearing_after_construction_is_rechecked_before_mapping_or_entry(self):
        volume=SyntheticCVolume(self.backing)
        with self.metadata(self.backing,mode=stat.S_IFDIR|0o700,attributes=0x400):
            with self.assertRaises(ValueError):volume.physical(volume.root)
            with self.assertRaises(ValueError):
                with volume:self.fail('changed backing entered')
        self.restored();self.assertEqual(list(self.backing.iterdir()),[])


if __name__=='__main__':unittest.main()
