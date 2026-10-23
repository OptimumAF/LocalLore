"""Independent adversarial warm IPC checks; synthetic only, no device or model."""
import base64
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import android_warm_spike as warm


SESSION = "0123456789abcdef" * 2
CANARY = "PRIVATE-WARM-REVIEW-731"


def worker(text="synthetic role text"):
    return dict(version=1, status="completed", text=text, error=None, load_ms=2,
                generation_ms=3, output_tokens=4, input_tokens=8,
                schema_enforced=False, thinking_disabled=True, template_applied=True)


def exchange(result=None, **changes):
    value = dict(version=1, session=SESSION, step=1, result=result or worker())
    value.update(changes)
    return json.dumps(value).encode()


def metrics(**changes):
    value = dict(worker_off_main=True, owners_balanced=True, generated_text_logged=False,
                 engines_opened=1, engines_closed=1, conversations_opened=2,
                 conversations_closed=2, main_pulses=3, warm_roles=2,
                 warm_engine_reused=True, warm_cancel_observed=False)
    value.update(changes)
    return value


def terminal(result=None, sdk=None):
    payload = json.dumps(result if result is not None else worker("")).encode()
    return (b"INSTRUMENTATION_RESULT: result_base64=" + base64.b64encode(payload)
            + b"\r\nINSTRUMENTATION_RESULT: metrics="
            + json.dumps(metrics() if sdk is None else sdk).encode() + b"\r\n")


class ExchangeReview(unittest.TestCase):
    def test_valid_private_result_round_trips_without_public_reencoding(self):
        self.assertEqual(warm.parse_exchange(exchange(), SESSION, 1), worker())

    def test_foreign_or_noncanonical_session_is_not_an_alias(self):
        for value in ("f" * 32, SESSION.upper(), "../" + SESSION, SESSION + "\n", True, None):
            with self.subTest(session=value):
                self.assertIsNone(warm.parse_exchange(exchange(session=value), SESSION, 1))

    def test_expected_session_and_step_are_also_strict(self):
        for session, step in ((SESSION.upper(), 1), (SESSION, True), (SESSION, 1.0),
                              (SESSION, "1"), (SESSION, 0), (SESSION, 3)):
            self.assertIsNone(warm.parse_exchange(exchange(), session, step))

    def test_unrelated_version_step_or_extra_envelope_fields_fail_closed(self):
        for key, value in (("version", True), ("version", 2), ("step", True),
                           ("step", 1.0), ("step", 2), ("private", CANARY)):
            self.assertIsNone(warm.parse_exchange(exchange(**{key: value}), SESSION, 1))

    def test_duplicate_keys_at_every_json_level_are_rejected(self):
        raw = exchange()
        for corrupt in (raw.replace(b'"version": 1', b'"version": 1, "version": 1', 1),
                        raw.replace(b'"step": 1', b'"step": 1, "step": 2'),
                        raw.replace(b'"text": "synthetic role text"', b'"text": "x", "text": "y"')):
            self.assertIsNone(warm.parse_exchange(corrupt, SESSION, 1))

    def test_invalid_encoding_oversize_and_excessively_nested_ipc_are_rejected(self):
        for raw in (b"\xff", exchange() + b" " * 131072, b"[" * 2000 + b"]" * 2000,
                    exchange().replace(b'"load_ms": 2', b'"load_ms": NaN')):
            self.assertIsNone(warm.parse_exchange(raw, SESSION, 1))

    def test_worker_protocol_is_not_weakened_by_exchange_wrapper(self):
        for change in (dict(text="x" * 16385), dict(output_tokens=True),
                       dict(thinking_disabled="true"), dict(status="error", error="private"),
                       dict(extra=CANARY)):
            self.assertIsNone(warm.parse_exchange(exchange(dict(worker(), **change)), SESSION, 1))


class TerminalReview(unittest.TestCase):
    def test_balanced_single_engine_two_role_terminal_is_valid(self):
        parsed = warm.terminal_result(terminal())
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed[0]["text"], "")
        self.assertEqual(parsed[1]["warm_roles"], 2)

    def test_terminal_cannot_repeat_private_role_output(self):
        self.assertIsNone(warm.terminal_result(terminal(result=worker(CANARY))))

    def test_completed_terminal_requires_exact_warm_owner_proofs(self):
        for key, value in (("engines_opened", 0), ("engines_closed", 0),
                           ("conversations_opened", 1), ("conversations_closed", 1),
                           ("warm_roles", 1), ("warm_roles", True), ("warm_roles", 2.0),
                           ("warm_engine_reused", False), ("warm_cancel_observed", True),
                           ("worker_off_main", False), ("main_pulses", 0)):
            with self.subTest(key=key, value=value):
                self.assertIsNone(warm.terminal_result(terminal(sdk=metrics(**{key: value}))))

    def test_boolean_counters_and_nonfinite_metadata_are_invalid(self):
        for key, value in (("engines_opened", True), ("warm_roles", float("nan")),
                           ("warm_roles", 10 ** 1000), ("warm_cancel_observed", 0)):
            self.assertIsNone(warm.terminal_result(terminal(sdk=metrics(**{key: value}))))

    def test_unlisted_metrics_and_exception_text_never_enter_public_projection(self):
        parsed = warm.terminal_result(terminal(sdk=metrics(exception=CANARY, path=CANARY)))
        self.assertIsNotNone(parsed)
        self.assertNotIn(CANARY, json.dumps(parsed[1]))

    def test_duplicate_terminal_records_never_become_success(self):
        raw = terminal()
        self.assertIsNone(warm.terminal_result(raw + raw))

    def test_abrupt_owner_termination_marker_cannot_accompany_success(self):
        self.assertIsNone(warm.terminal_result(terminal(sdk=metrics(cleanup_requires_process_termination=True))))


def request(role):
    return dict(version=1, role=role, prompt="synthetic trusted fixture", schema=None,
                max_tokens=350 if role == "director" else 220, context_tokens=4096, threads=4)


class SyntheticSession:
    def __init__(self, trace, final=None, outputs=None):
        self.trace = trace
        self.outputs = list(outputs or [worker(CANARY + " proposal"), worker(CANARY + " narration")])
        self.final = final or dict(status="completed", cleanup_complete=True,
                                  adb_cleanup_complete=True, directory_cleanup_complete=True, sdk=metrics())
        self.expired = False

    def check_budget(self):
        if self.expired:
            raise warm.WarmFailure("timeout", "wait_result")

    def generate(self, trusted):
        self.trace.append(trusted["role"])
        value = self.outputs.pop(0)
        if isinstance(value, Exception):
            raise value
        return value

    def finish(self):
        self.trace.append("finish")
        return self.final


class CoordinatorReview(unittest.TestCase):
    def run_case(self, session=None, validate=None, commit=None, after_validate=None):
        trace = session.trace if session is not None else []
        session = session or SyntheticSession(trace)
        def oracle(native, binary, operation, case, data=b""):
            trace.append(operation)
            if operation == "fixture":
                return dict(director=request("director"), preflight_error=None)
            if operation == "validate":
                if after_validate:
                    after_validate(session)
                return validate or dict(status="accepted", narrator=request("narrator"), canonical_unchanged=True)
            if operation == "commit":
                return commit or dict(status="committed", revision=1, events=1, recipient_observations=1,
                                      absent_observations=0, exact_retry_unchanged=True)
            raise AssertionError(operation)
        with patch.object(warm.spike, "oracle", side_effect=oracle):
            report = warm.run_warm(session, None, "synthetic-oracle")
        return report, trace

    def test_commit_follows_both_roles_rust_validation_and_final_cleanup(self):
        report, trace = self.run_case()
        self.assertEqual(trace, ["fixture", "director", "validate", "narrator", "finish", "commit"])
        self.assertEqual(report["status"], "committed")
        self.assertNotIn(CANARY, json.dumps(report))

    def test_rejected_director_never_reaches_narrator_or_commit(self):
        report, trace = self.run_case(validate=dict(status="rejected", error=CANARY))
        self.assertEqual(trace, ["fixture", "director", "validate", "finish"])
        self.assertEqual(report["status"], "engine_rejected")
        self.assertNotIn(CANARY, json.dumps(report))

    def test_cancellation_never_validates_or_commits_a_partial_role(self):
        trace = []
        session = SyntheticSession(trace, outputs=[warm.WarmFailure("cancelled", "wait_result")])
        report, trace = self.run_case(session)
        self.assertEqual(trace, ["fixture", "director", "finish"])
        self.assertEqual(report["status"], "cancelled")

    def test_deadline_expired_by_validation_never_publishes_narrator(self):
        report, trace = self.run_case(after_validate=lambda session: setattr(session, "expired", True))
        self.assertEqual(trace, ["fixture", "director", "validate", "finish"])
        self.assertEqual(report["status"], "timeout")

    def test_each_cleanup_proof_is_independently_required_for_commit(self):
        for key in ("cleanup_complete", "adb_cleanup_complete", "directory_cleanup_complete"):
            for invalid in (False, 1, "true", None):
                trace = []
                session = SyntheticSession(trace)
                session.final[key] = invalid
                report, trace = self.run_case(session)
                self.assertNotIn("commit", trace)
                self.assertEqual(report["status"], "cleanup_failed")

    def test_defective_adapter_metadata_cannot_leak_private_data(self):
        session = SyntheticSession([])
        session.final.update(exception=CANARY, stage=CANARY, nested={CANARY: CANARY})
        session.final["sdk"]["private_prompt"] = CANARY
        report, _ = self.run_case(session)
        self.assertNotIn(CANARY, json.dumps(report))

    def test_cancellation_observed_by_adapter_is_never_committable(self):
        session = SyntheticSession([])
        session.final["sdk"]["warm_cancel_observed"] = True
        report, trace = self.run_case(session)
        self.assertNotIn("commit", trace)
        self.assertNotEqual(report["status"], "committed")

    def test_host_cancellation_request_prevents_commit_even_before_sdk_observes_it(self):
        session = SyntheticSession([])
        session.final["cancel_requested"] = True
        report, trace = self.run_case(session)
        self.assertNotIn("commit", trace)
        self.assertNotEqual(report["status"], "committed")

    def test_wrong_narrator_request_from_defective_oracle_does_not_release_role(self):
        report, trace = self.run_case(validate=dict(status="accepted", narrator=request("director")))
        self.assertEqual(trace, ["fixture", "director", "validate", "finish"])
        self.assertNotEqual(report["status"], "committed")

    def test_commit_reply_boolean_revision_is_not_the_integer_one(self):
        reply = dict(status="committed", revision=True, events=1, recipient_observations=1,
                     absent_observations=0, exact_retry_unchanged=True)
        report, _ = self.run_case(commit=reply)
        self.assertEqual(report["status"], "engine_rejected")

    def test_preflight_rejection_with_no_director_never_allocates_a_model(self):
        session = SyntheticSession([])
        rejection = next(iter(warm.spike.host.DOMAIN_ERRORS))
        with patch.object(warm.spike, "oracle", return_value=dict(preflight_error=rejection, director=None)):
            report = warm.run_warm(session, None, "synthetic-oracle", case="spent")
        self.assertEqual(report["status"], "preflight_rejected")
        self.assertEqual(report["attempted_roles"], 0)
        self.assertEqual(session.trace, ["finish"])


class LifecycleReview(unittest.TestCase):
    def session(self):
        device = SimpleNamespace(shell=lambda *args, **kwargs: b"")
        session = warm.WarmSdkSession(device, "1" * 64)
        session.sdk = SimpleNamespace(verify_package=lambda: None, stop=lambda: True)
        return session

    def test_unknown_clean_start_client_cannot_become_drained_after_a_retry(self):
        session = self.session()
        calls = 0
        def stop():
            nonlocal calls
            calls += 1
            if calls == 1:
                raise warm.spike.Failure("device_command_failed", command_cleaned=False)
            return True
        session.sdk.stop = stop
        with self.assertRaises(Exception):
            session.start()
        final = session.finish()
        self.assertFalse(final["adb_cleanup_complete"])

    def test_unknown_publish_identity_client_retains_owned_directory(self):
        session = self.session()
        session.created = True
        calls = []
        session.owned = lambda: None
        session.private = lambda command, **kwargs: calls.append(command) or b""
        session.sdk.verify_package = lambda: (_ for _ in ()).throw(
            warm.spike.Failure("device_command_failed", command_cleaned=False))
        with self.assertRaises(Exception):
            session.publish("request-1.json", b"synthetic")
        final = session.finish()
        self.assertFalse(final["adb_cleanup_complete"])
        self.assertFalse(final["directory_cleanup_complete"])
        self.assertFalse(any("rmdir" in call or "rm -f" in call for call in calls))

    def test_undrained_launcher_is_joined_before_stop_and_prevents_directory_deletion(self):
        session = self.session()
        trace = []
        session.created = True
        session.step = 2
        session.launcher = SimpleNamespace(ident=1, join=lambda **kwargs: trace.append("join"), is_alive=lambda: False)
        session.finished.set()
        session.results.append(SimpleNamespace(cleanup_complete=False, status="completed", returncode=0,
                                               stdout=terminal()))
        session.sdk.stop = lambda: trace.append("stop") or True
        session.owned = lambda: None
        session.private = lambda command, **kwargs: trace.append(command) or b""
        final = session.finish()
        self.assertLess(trace.index("join"), trace.index("stop"))
        self.assertFalse(final["cleanup_complete"])
        self.assertFalse(final["adb_cleanup_complete"])
        self.assertFalse(final["directory_cleanup_complete"])
        self.assertFalse(any("rmdir" in call or "rm -f" in call for call in trace))

    def test_final_owner_metrics_never_substitute_for_failed_package_absence(self):
        session = self.session()
        session.created = True
        session.step = 2
        session.launcher = SimpleNamespace(ident=1, join=lambda **kwargs: None, is_alive=lambda: False)
        session.finished.set()
        session.results.append(SimpleNamespace(cleanup_complete=True, status="completed", returncode=0,
                                               stdout=terminal()))
        session.sdk.stop = lambda: False
        final = session.finish()
        self.assertEqual(final["status"], "cleanup_failed")
        self.assertFalse(final["cleanup_complete"])
        self.assertFalse(final["directory_cleanup_complete"])

    def test_third_role_is_rejected_before_publication_or_launch(self):
        session = self.session()
        session.step = 2
        session.publish = unittest.mock.Mock()
        with self.assertRaises(warm.WarmFailure):
            session.generate(request("narrator"))
        session.publish.assert_not_called()

    def test_wrong_role_is_rejected_before_creating_the_first_session(self):
        session = self.session()
        session.start = unittest.mock.Mock()
        with self.assertRaises(warm.WarmFailure):
            session.generate(request("narrator"))
        session.start.assert_not_called()

    def test_existing_out_of_order_result_is_not_a_successful_first_role(self):
        session = self.session()
        session.start = lambda: None
        session.read = lambda name: b"forged" if name == "result-2.json" else b""
        session.publish = unittest.mock.Mock()
        with self.assertRaises(warm.WarmFailure):
            session.generate(request("director"))
        session.publish.assert_not_called()

    def test_finish_is_idempotent_and_never_repeats_stop_or_file_cleanup(self):
        session = self.session()
        session.sdk.stop = unittest.mock.Mock(return_value=True)
        first = session.finish()
        self.assertEqual(session.finish(), first)
        self.assertEqual(session.sdk.stop.call_count, 1)

    def test_budget_expiring_during_request_transfer_never_starts_instrumentation(self):
        session = self.session()
        session.start = lambda: None
        session.read = lambda name: b""
        expired = False
        def budget():
            if expired:
                raise warm.WarmFailure("timeout", "publish_request")
        def publish(name, data):
            nonlocal expired
            expired = True
        session.check_budget, session.publish = budget, publish
        with patch.object(warm.threading, "Thread") as constructor:
            with self.assertRaises(warm.WarmFailure):
                session.generate(request("director"))
            constructor.assert_not_called()

    def test_final_result_published_during_empty_read_is_reread_after_launcher_exit(self):
        session = self.session()
        session.step = 1
        session.launcher = object()
        session.publish = lambda name, data: None
        result_reads = 0
        def read(name):
            nonlocal result_reads
            if name != "result-2.json":
                return b""
            result_reads += 1
            # The first lookup is the before-publication out-of-order guard.
            # On the first poll, publication/exit races the reader's empty result.
            if result_reads <= 2:
                if result_reads == 2:
                    session.finished.set()
                return b""
            return exchange(session=session.session_id, step=2)
        session.read = read
        self.assertEqual(session.generate(request("narrator")), worker())
        self.assertEqual(session.step, 2)
        self.assertEqual(result_reads, 3)


if __name__ == "__main__":
    unittest.main()
