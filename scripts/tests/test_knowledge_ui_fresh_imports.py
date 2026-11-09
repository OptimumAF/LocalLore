"""Original startup namespace regression; only explicit loader/module ports.

No frozen inspector, installed tool, profile, SDK or operational API is executed.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import ExitStack
import copy
from pathlib import Path, PureWindowsPath
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

from scripts import knowledge_ui_fresh_contract as rules
from scripts import run_knowledge_ui_fresh as bridge


class NamespaceRefused(ValueError):
    pass


class PartsPorts:
    """Model namespace search locations dynamically, never read real paths."""
    def __enter__(self):
        self.stack=ExitStack();self.checks=[];self.loads=[];self.gits=[]
        self.root=bridge.ROOT;self.source=rules.SOURCE
        clean=[p for p in sys.path if p and PureWindowsPath(p) not in
               (PureWindowsPath(self.root),PureWindowsPath(self.source))]
        self.stack.enter_context(patch.object(sys,'path',clean))
        self.stack.enter_context(patch.dict(sys.modules))
        for name in tuple(sys.modules):
            if name=='benchmarks' or name.startswith('benchmarks.'):
                del sys.modules[name]
        package=ModuleType('benchmarks');package.__file__=None
        owner=self
        class Locations:
            def __iter__(self):
                # This is the relevant namespace-import rule: each parent on
                # sys.path contributes its benchmarks directory. An added Root
                # must become visible instead of a frozen fabricated list.
                for parent in sys.path:
                    if PureWindowsPath(parent) in (PureWindowsPath(owner.source),PureWindowsPath(owner.root)):
                        yield str(Path(parent)/'benchmarks')
        package.__path__=Locations();sys.modules['benchmarks']=package
        for short in ('isolated_adb_lease','prepare_recovery_contract','knowledge_ui_profile_build'):
            module=ModuleType('benchmarks.'+short)
            module.__file__=str(self.source/'benchmarks'/(short+'.py'))
            setattr(package,short,module);sys.modules[module.__name__]=module
        self.api=SimpleNamespace(env=object(),build=object(),probe=object(),
            storage=SimpleNamespace(DEFAULT_REGISTRY=rules.REGISTRY),
            activation=SimpleNamespace(SOURCE_ROOT=self.source,RUNTIME=rules.RUNTIME,CONTROLS=rules.CONTROLS),
            contract=SimpleNamespace(GUEST_ROOT=str(rules.GUEST),CLIENT_VERSION=16,MODEL_MATERIAL=False))
        self.inspector=ModuleType('_sdk16_frozen_inspector')
        self.inspector.__file__=str(rules.INSPECTOR_ROOT/'scripts/freeze_knowledge_ui_prepare_inputs.py')
        self.inspector._MODULES=None
        self.inspector._git=lambda root,head:self.gits.append((root,head))
        self.inspector._api=self.namespace_checked_api
        self.stack.enter_context(patch.object(bridge,'_MODULES',None))
        # Reset the newly specified cache, without requiring its existence in
        # an archived baseline that loaded scripts.contract through sys.path.
        self.stack.enter_context(patch.object(bridge,'_RULES',None,create=True))
        self.stack.enter_context(patch.object(Path,'resolve',lambda path,*a,**k:path))
        self.stack.enter_context(patch.object(bridge.importlib.util,'spec_from_file_location',side_effect=self.spec))
        self.stack.enter_context(patch.object(bridge.importlib.util,'module_from_spec',side_effect=self.module))
        return self

    def __exit__(self,*error):
        self.stack.close()

    def namespace_checked_api(self):
        if str(self.source) not in sys.path:sys.path.insert(0,str(self.source))
        locations=list(sys.modules['benchmarks'].__path__)
        self.checks.append(copy.deepcopy(locations))
        if locations!=[str(self.source/'benchmarks')]:
            raise NamespaceRefused('module_source')
        for name,module in tuple(sys.modules.items()):
            if name.startswith('benchmarks.'):
                file=getattr(module,'__file__',None)
                if file is None or PureWindowsPath(file).parent!=PureWindowsPath(self.source/'benchmarks'):
                    raise NamespaceRefused('module_source')
        return self.api

    def spec(self,name,path):
        path=Path(path)
        allowed={rules.CONTRACT:'contract',rules.INSPECTOR_ROOT/'scripts/freeze_knowledge_ui_prepare_inputs.py':'inspector'}
        if path not in allowed:raise AssertionError('unexpected loader path')
        self.loads.append((name,path))
        return SimpleNamespace(name=name,path=path,role=allowed[path],loader=SimpleNamespace(exec_module=self.populate))

    def module(self,spec):
        module=ModuleType(spec.name);module.__file__=str(spec.path);module._test_role=spec.role
        return module

    def populate(self,module):
        if module._test_role=='contract':
            for name,value in vars(rules).items():
                if not name.startswith('__'):setattr(module,name,value)
            module.__file__=str(rules.CONTRACT)
        elif module._test_role=='inspector':
            for name,value in vars(self.inspector).items():
                if not name.startswith('__'):setattr(module,name,value)
        else:raise AssertionError('unexpected module role')


class FreshPartsNamespaceTests(unittest.TestCase):
    def test_parts_does_not_add_operator_root_to_frozen_benchmark_namespace(self):
        with PartsPorts() as ports:
            accepted_rules,api=bridge._parts()
            self.assertEqual(accepted_rules.SOURCE,rules.SOURCE)
            self.assertIs(api.env,ports.api.env)
            self.assertNotIn(str(ports.root),sys.path)
            self.assertEqual(ports.checks,[[str(ports.source/'benchmarks')]]*2)
            self.assertEqual(ports.gits,[(rules.INSPECTOR_ROOT,rules.INSPECTOR_HEAD),(rules.SOURCE,rules.SOURCE_HEAD)])
            self.assertTrue(any(path==rules.INSPECTOR_ROOT/'scripts/freeze_knowledge_ui_prepare_inputs.py'
                                for name,path in ports.loads))

    def test_parts_still_refuses_a_cached_foreign_transitive_benchmark_module(self):
        with PartsPorts() as ports:
            borrowed=ModuleType('benchmarks.foreign_cached_worker')
            borrowed.__file__=str(ports.root/'benchmarks/foreign_cached_worker.py')
            sys.modules[borrowed.__name__]=borrowed
            with self.assertRaisesRegex(NamespaceRefused,'^module_source$'):
                bridge._parts()
            self.assertTrue(ports.checks,'frozen transitive module guard must run')
            self.assertNotIn(str(ports.root),sys.path)
            self.assertIsNone(bridge._MODULES,'refusal cannot cache a qualified operational API')


if __name__=='__main__':
    unittest.main()
