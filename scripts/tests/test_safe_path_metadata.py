"""Original safe-path metadata fixtures, with no real symlinks or privileges."""
import errno
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from benchmarks import receipt_avd_environment as env


class Node:
    def __init__(self,text,*,mode=stat.S_IFDIR,attributes=0,exists=True,error=None):
        self.text=text;self.mode=mode;self.attributes=attributes;self.present=exists;self.error=error
        self.parents=();self.calls=[]
    def __str__(self):return self.text
    def is_absolute(self):return True
    def exists(self):
        self.calls.append('exists')
        # Python 3.14 exists()/is_symlink() report false for inaccessible
        # metadata. A no-follow lstat must still expose the actual failure.
        return self.present and self.error is None
    def is_symlink(self):self.calls.append('is_symlink');return self.error is None and stat.S_ISLNK(self.mode)
    def lstat(self):
        self.calls.append('lstat')
        if self.error is not None:raise self.error
        if not self.present and not stat.S_ISLNK(self.mode):raise FileNotFoundError(errno.ENOENT,'original synthetic missing node')
        return SimpleNamespace(st_mode=self.mode,st_file_attributes=self.attributes)
    def is_file(self):self.calls.append('is_file');return self.present and stat.S_ISREG(self.mode)
    def is_dir(self):self.calls.append('is_dir');return self.present and stat.S_ISDIR(self.mode)


class Chain:
    def __init__(self):
        target=Path('D:/Synthetic/safe-metadata/parent/target')
        self.nodes=[Node(str(target),mode=stat.S_IFREG),*[Node(str(parent))for parent in target.parents]]
        self.target=self.nodes[0];self.target.parents=tuple(self.nodes[1:])
    def check(self,*,exists=True,directory=False):
        with patch.object(env,'Path',return_value=self.target):
            return env.safe_path(str(self.target),exists=exists,directory=directory)


class SafePathMetadataTests(unittest.TestCase):
    def refused(self,call):
        with self.assertRaises((env.EnvironmentRefused,OSError)):call()

    def test_real_D_file_and_directory_keep_existing_target_type_semantics(self):
        base=Path(tempfile.mkdtemp(prefix='locallore-safe-metadata-',dir='D:/Dev/_Temp'))
        file=base/'original.txt';file.write_bytes(b'original safe-path fixture\0\x1a')
        self.assertEqual(env.safe_path(file),file);self.assertEqual(env.safe_path(base,directory=True),base)
        self.refused(lambda:env.safe_path(file,directory=True));self.refused(lambda:env.safe_path(base))
        # exists=False admits a canonical future path and ignores target type.
        self.assertEqual(env.safe_path(file,exists=False,directory=True),file)

    def test_real_D_missing_target_and_missing_intermediate_parent_remain_admissible_only_when_optional(self):
        base=Path(tempfile.mkdtemp(prefix='locallore-safe-metadata-',dir='D:/Dev/_Temp'))
        for future in(base/'not-created',base/'missing-parent'/'not-created'):
            self.assertEqual(env.safe_path(future,exists=False),future)
            self.refused(lambda:env.safe_path(future));self.refused(lambda:env.safe_path(future,directory=True))
            self.assertFalse(future.exists())

    def test_relative_or_noncanonical_parent_traversal_refuses_before_metadata_inspection(self):
        base=Path(tempfile.mkdtemp(prefix='locallore-safe-metadata-',dir='D:/Dev/_Temp'))
        with patch.object(Path,'lstat',side_effect=AssertionError('metadata reached before lexical admission')):
            self.refused(lambda:env.safe_path('relative-path',exists=False))
            self.refused(lambda:env.safe_path(base/'child'/'..'/'target',exists=False))

    def test_optional_target_uses_one_fresh_no_follow_stat_per_ancestor_without_following_probes(self):
        chain=Chain();self.assertIs(chain.check(exists=False),chain.target)
        for node in chain.nodes:
            with self.subTest(node=str(node)):
                self.assertEqual(node.calls,['lstat'])

    def test_required_file_retains_final_target_exists_and_file_checks_without_ancestor_double_probes(self):
        chain=Chain();self.assertIs(chain.check(),chain.target)
        self.assertEqual(chain.target.calls,['lstat','exists','is_file'])
        for node in chain.nodes[1:]:self.assertEqual(node.calls,['lstat'])

    def test_required_directory_retains_final_target_directory_check(self):
        chain=Chain();chain.target.mode=stat.S_IFDIR;self.assertIs(chain.check(directory=True),chain.target)
        self.assertEqual(chain.target.calls,['lstat','exists','is_dir'])
        for node in chain.nodes[1:]:self.assertEqual(node.calls,['lstat'])

    def test_synthetic_posix_symlink_and_broken_symlink_refuse_at_target_or_ancestor(self):
        for index in(0,1,3):
            for broken in(False,True):
                with self.subTest(index=index,broken=broken):
                    chain=Chain();node=chain.nodes[index];node.mode=stat.S_IFLNK;node.present=not broken
                    self.refused(lambda:chain.check(exists=False))
                    self.assertTrue(all(not node.calls for node in chain.nodes[index+1:]))

    def test_synthetic_windows_reparse_attribute_refuses_without_target_type_or_later_checks(self):
        for index in(0,1,3):
            chain=Chain();chain.nodes[index].attributes=0x400
            with self.subTest(index=index):
                self.refused(lambda:chain.check(exists=False))
                self.assertTrue(all(not node.calls for node in chain.nodes[index+1:]))
                self.assertNotIn('is_file',chain.target.calls)

    def test_link_or_reparse_appearing_between_calls_is_not_hidden_by_a_cache(self):
        for change in('symlink','reparse'):
            chain=Chain();self.assertIs(chain.check(exists=False),chain.target)
            if change=='symlink':chain.nodes[1].mode=stat.S_IFLNK
            else:chain.nodes[1].attributes=0x400
            with self.subTest(change=change):
                self.refused(lambda:chain.check(exists=False))
                self.assertEqual(chain.target.calls.count('lstat'),2);self.assertEqual(chain.nodes[1].calls.count('lstat'),2)

    def test_repeated_safe_calls_reinspect_each_ancestor_without_persistent_metadata_cache(self):
        chain=Chain();chain.check(exists=False);chain.check(exists=False)
        for node in chain.nodes:self.assertEqual(node.calls.count('lstat'),2)

    def test_uninspectable_permission_ancestor_fails_closed_before_higher_ancestors_or_target_checks(self):
        chain=Chain();chain.nodes[1].error=PermissionError(errno.EACCES,'original synthetic denied metadata')
        self.refused(lambda:chain.check())
        self.assertTrue(all(not node.calls for node in chain.nodes[2:]));self.assertNotIn('is_file',chain.target.calls)

    def test_uninspectable_device_error_is_not_reinterpreted_as_an_absent_ancestor(self):
        chain=Chain();chain.nodes[2].error=OSError(errno.EIO,'original synthetic metadata device error')
        self.refused(lambda:chain.check(exists=False))
        self.assertTrue(all(not node.calls for node in chain.nodes[3:]));self.assertNotIn('is_file',chain.target.calls)


if __name__=='__main__':unittest.main()
