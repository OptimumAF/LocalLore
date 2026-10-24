// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
package org.locallore.runtimebench.litert;

import static org.junit.Assert.*;
import com.google.gson.JsonObject;
import java.util.Arrays;
import java.util.HashSet;
import org.junit.Test;

public final class RoleObservationTest {
    @Test public void rawZeroCountsAreReportedWithoutInventingTokenProgress() {
        JsonObject value = new RoleObservation(0, 0, "none", true, 0, 0).toJson();
        assertTrue(value.get("benchmark_available").getAsBoolean());
        assertEquals(0, value.get("sdk_input_tokens").getAsInt());
        assertTrue(value.get("configuration").isJsonNull());
        assertEquals(new HashSet<>(Arrays.asList("version", "callback_messages", "buffered_text_bytes", "callback_error",
            "benchmark_available", "sdk_input_tokens", "sdk_output_tokens", "configuration")), value.keySet());
        JsonObject unavailable = new RoleObservation(0, 0, "none", false, null, null).toJson();
        assertTrue(unavailable.get("sdk_input_tokens").isJsonNull());
    }
    @Test public void diagnosticCountsCanExceedTheGameplayContextWithoutAuthorizingAnything() {
        JsonObject value = new RoleObservation(65535, 16384, "output_too_large", true, Integer.MAX_VALUE, Integer.MAX_VALUE).toJson();
        assertEquals(Integer.MAX_VALUE, value.get("sdk_output_tokens").getAsInt());
        assertEquals("output_too_large", value.get("callback_error").getAsString());
    }
    @Test public void invalidSnapshotsAreRejectedWithoutExceptionProse() {
        invalid(() -> new RoleObservation(-1, 0, "none", false, null, null));
        invalid(() -> new RoleObservation(65536, 0, "none", false, null, null));
        invalid(() -> new RoleObservation(0, 1, "none", false, null, null));
        invalid(() -> new RoleObservation(1, 16385, "none", false, null, null));
        invalid(() -> new RoleObservation(1, 0, "private story", false, null, null));
        invalid(() -> new RoleObservation(1, 0, "none", false, 0, 0));
        invalid(() -> new RoleObservation(1, 0, "none", true, null, 0));
        invalid(() -> new RoleObservation(1, 0, "none", true, -1, 0));
    }
    @Test public void requestedConfigurationContainsOnlyBoundedMetadataAndCopiesAreIndependent() {
        RoleObservation.Config config = new RoleObservation.Config(true, true, true, 350, 32768, 32768);
        RoleObservation observation = new RoleObservation(1, 3, "none", false, null, null, config);
        JsonObject first = observation.toJson(); first.getAsJsonObject("configuration").addProperty("private", "canary");
        JsonObject next = observation.toJson(); assertFalse(next.getAsJsonObject("configuration").has("private"));
        assertEquals(6, next.getAsJsonObject("configuration").size());
        invalid(() -> new RoleObservation.Config(false, true, true, 350, 1, 1));
        invalid(() -> new RoleObservation.Config(true, true, true, 350, 1, 0));
        invalid(() -> new RoleObservation.Config(false, true, true, 351, 1, 0));
        invalid(() -> new RoleObservation.Config(false, true, true, 1, 0, 0));
    }
    private static void invalid(Runnable test) {
        try { test.run(); fail("expected bounded invalid observation"); }
        catch (IllegalArgumentException expected) { assertEquals("invalid_role_observation", expected.getMessage()); }
    }
}
