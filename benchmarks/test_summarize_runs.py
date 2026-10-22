"""Calculator tests use invented numbers, never device/model performance evidence."""
import copy
import unittest

from summarize_runs import PROVENANCE, TIMINGS, summarize


def sample(turn_id="unit-1", duration=100):
    row = dict.fromkeys(PROVENANCE, "unit-test-placeholder")
    row.update(app_commit="a" * 40, runtime_commit="b" * 40, model_sha256="c" * 64)
    row.update(dict.fromkeys(TIMINGS, 1))
    row.update(kind="real_model_measurement", environment="host", condition="warm",
               turn_id=turn_id, turn_ms=duration, first_final_response_ms=duration,
               schema_valid_before_repair=True, proposal_accepted=True, repaired=False,
               narrator_faithful=True, repair_count=0, peak_memory_bytes=None)
    return row


class AggregateTests(unittest.TestCase):
    def test_nearest_rank_and_missing_memory_denominator(self):
        rows = [sample(f"unit-{i}", i + 10) for i in range(20)]
        rows[0]["peak_memory_bytes"] = 99
        result = summarize(rows)
        self.assertEqual(result["timings_ms"]["turn_ms"], {"p50": 19, "p95": 28})
        self.assertEqual(result["peak_memory_bytes"], {"max_observed": 99, "observed_count": 1})
        self.assertEqual(result["sample_count"], 20)

    def test_empty_and_duplicate_samples_fail(self):
        for rows in ([], [sample(), sample()]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                summarize(rows)

    def test_fake_and_mixed_profiles_fail(self):
        for changed in ({"kind": "fake_provider"}, {"environment": "physical_android"},
                        {"runtime_commit": "different"}, {"condition": "cold"}):
            row = sample("unit-2")
            row.update(changed)
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                summarize([sample(), row])

    def test_bad_measurements_and_unbounded_repairs_fail(self):
        for changed in ({"turn_ms": float("nan")}, {"director_decode_ms": -1},
                        {"repair_ms": True}, {"proposal_accepted": 1},
                        {"first_final_response_ms": 0}, {"commit_ms": 1000},
                        {"repair_count": 2}, {"repair_count": 1}, {"model_sha256": ""}):
            row = copy.deepcopy(sample())
            row.update(changed)
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                summarize([row])


if __name__ == "__main__":
    unittest.main()
