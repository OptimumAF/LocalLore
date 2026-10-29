"""Private cProfile observations; no validation or execution authority.

Snapshots contain function identities and aggregate costs only, never caller
arguments, locals or return values. Full filenames belong in private evidence;
callers must sanitize any public aggregate export. Observed costs include the
profiler's overhead and are not an estimate of unprofiled execution time.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import cProfile
import pstats
import sys
import time


class ProfileCapture:
    """Observe one cooperative action without replacing another profiler.

    Monitoring tool names/masks identify cooperative ownership only: they do
    not authenticate malicious same-name callback replacement or grant any
    execution/validation authority.
    """

    def __init__(self):
        self._state = "new"
        self._profile = None
        self._result = None
        self._wall_start = self._cpu_start = None
        self._monitoring = getattr(sys, "monitoring", None)
        self._backend = self._events = None

    def _owns_hook(self):
        if self._backend == "monitoring":
            return (self._monitoring.get_tool(self._monitoring.PROFILER_ID) == "cProfile" and
                    self._monitoring.get_events(self._monitoring.PROFILER_ID) == self._events)
        return sys.getprofile() is self._profile

    def __enter__(self):
        if self._state != "new":
            raise ValueError("profile_lifecycle")
        self._state = "entering"
        if (sys.getprofile() is not None or
                self._monitoring is not None and
                self._monitoring.get_tool(self._monitoring.PROFILER_ID) is not None):
            self._state = "failed"
            raise ValueError("profile_already_active")
        # The built-in monotonic timer avoids an extra Python timer callback
        # per profiling event. pstats seconds are rounded to integer ns below.
        self._profile = cProfile.Profile()
        try:
            self._wall_start = time.perf_counter_ns()
            self._cpu_start = time.process_time_ns()
            self._profile.enable()
            if sys.getprofile() is self._profile:
                self._backend = "legacy"
            elif (sys.getprofile() is None and self._monitoring is not None and
                  self._monitoring.get_tool(self._monitoring.PROFILER_ID) == "cProfile"):
                self._backend = "monitoring"
                self._events = self._monitoring.get_events(self._monitoring.PROFILER_ID)
            else:
                raise ValueError("profile_changed")
        except BaseException:
            self._state = "failed"
            if self._owns_hook():
                self._profile.disable()
            raise
        self._state = "active"
        return self

    def __exit__(self, exc_type, exc, traceback):
        if self._state != "active":
            raise ValueError("profile_lifecycle")
        self._state = "closing"
        try:
            # On Python's monitoring backend sys.getprofile() remains None;
            # a later legacy callback can coexist but invalidates this sample.
            expected = self._profile if self._backend == "legacy" else None
            if sys.getprofile() is not expected or not self._owns_hook():
                raise ValueError("profile_changed")
            self._profile.disable()
            cpu_end = time.process_time_ns()
            wall_end = time.perf_counter_ns()
            stats = pstats.Stats(self._profile).stats
            entries = []
            for (filename, line, function), (primitive, calls, own, cumulative, _) in stats.items():
                entries.append(dict(filename=filename, line=line, function=function,
                                    primitive_calls=primitive, calls=calls,
                                    self_ns=round(own * 1_000_000_000),
                                    cumulative_ns=round(cumulative * 1_000_000_000)))
            entries.sort(key=lambda entry: (entry["filename"], entry["line"], entry["function"]))
            self._result = dict(version=1, scope="python-cprofile-cost-v1",
                                wall_ns=wall_end - self._wall_start,
                                cpu_ns=cpu_end - self._cpu_start,
                                total_calls=sum(entry["calls"] for entry in entries),
                                primitive_calls=sum(entry["primitive_calls"] for entry in entries),
                                entries=entries)
            self._state = "closed"
        except BaseException:
            self._state = "failed"
            self._result = None
            # Observation failures must not replace the action's exception,
            # including cancellation, KeyboardInterrupt or SystemExit.
            if exc_type is None:
                raise
        finally:
            # Disabling our monitoring collector leaves an action-installed
            # legacy callback untouched; a legacy replacement is not ours.
            if self._owns_hook():
                try:
                    self._profile.disable()
                except BaseException:
                    self._state = "failed"
                    self._result = None
                    if exc_type is None:
                        raise
        return False

    def snapshot(self):
        """Return an independent observation after this single context closes."""
        if self._state != "closed":
            raise ValueError("profile_lifecycle")
        return copy.deepcopy(self._result)
