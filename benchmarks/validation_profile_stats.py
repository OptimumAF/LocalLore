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
    """Observe one current-thread action without replacing another profiler."""

    def __init__(self):
        self._state = "new"
        self._profile = None
        self._result = None
        self._wall_start = self._cpu_start = None

    def __enter__(self):
        if self._state != "new":
            raise ValueError("profile_lifecycle")
        self._state = "entering"
        if sys.getprofile() is not None:
            self._state = "failed"
            raise ValueError("profile_already_active")
        self._profile = cProfile.Profile(timer=time.perf_counter_ns, timeunit=1e-9)
        try:
            self._wall_start = time.perf_counter_ns()
            self._cpu_start = time.process_time_ns()
            self._profile.enable()
        except BaseException:
            self._state = "failed"
            if sys.getprofile() is self._profile:
                self._profile.disable()
            raise
        self._state = "active"
        return self

    def __exit__(self, exc_type, exc, traceback):
        if self._state != "active":
            raise ValueError("profile_lifecycle")
        self._state = "closing"
        try:
            # A replacement installed by the action belongs to that action.
            # Our profiler is already detached: do not disable its successor.
            if sys.getprofile() is not self._profile:
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
            # Only detach our own hook. Never clear a profiler installed by
            # the action while this context was active.
            if sys.getprofile() is self._profile:
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
