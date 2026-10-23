// Copyright 2026 LocalLore contributors.
// SPDX-License-Identifier: Apache-2.0
package org.locallore.runtimebench.litert;

import static org.junit.Assert.*;
import com.google.ai.edge.litertlm.Contents;
import com.google.ai.edge.litertlm.Message;
import com.google.ai.edge.litertlm.Role;
import java.util.Collections;
import org.junit.Test;

/** Actual SDK value objects; no native engine or model is loaded. */
public class StreamTest {
    private Message visible(String value) {
        return new Message(Role.MODEL, Contents.Companion.of(value), Collections.emptyList(), Collections.emptyMap());
    }
    @Test public void exposedChannelCannotBeRetainedAlongsideVisibleText() {
        SpikeInstrumentation.Stream stream = new SpikeInstrumentation.Stream();
        stream.onMessage(new Message(Role.MODEL, Contents.Companion.of("visible"), Collections.emptyList(), Collections.singletonMap("thought", "synthetic-hidden-text")));
        stream.onDone();
        Exception error = assertThrows(Exception.class, stream::text);
        assertEquals("unsupported_output", error.getMessage());
    }
    @Test public void splitOrClosingThinkingTagsAreRejectedAfterAssembly() {
        for (String[] chunks : new String[][]{{"<thi", "nk>synthetic"}, {"visible", "</think>"}, {"<THINK>", "synthetic"}}) {
            SpikeInstrumentation.Stream stream = new SpikeInstrumentation.Stream();
            for (String chunk : chunks) stream.onMessage(visible(chunk));
            stream.onDone();
            assertEquals("unsupported_output", assertThrows(Exception.class, stream::text).getMessage());
        }
    }
    @Test public void ordinaryBoundedVisibleContentIsReturned() throws Exception {
        SpikeInstrumentation.Stream stream = new SpikeInstrumentation.Stream();
        stream.onMessage(visible("Lan")); stream.onMessage(visible("tern.")); stream.onDone();
        assertEquals("Lantern.", stream.text());
    }
    @Test public void oversizedUtf8CannotBeReturned() {
        SpikeInstrumentation.Stream stream = new SpikeInstrumentation.Stream();
        stream.onMessage(visible("é".repeat(8193))); stream.onDone();
        assertEquals("output_too_large", assertThrows(Exception.class, stream::text).getMessage());
    }
    @Test public void terminalLatchesWithoutContentNeverCountAsObservedOutput() {
        SpikeInstrumentation.Stream done = new SpikeInstrumentation.Stream(); done.onDone();
        assertEquals(0, done.first.getCount()); assertFalse(done.hasOutput());
        SpikeInstrumentation.Stream error = new SpikeInstrumentation.Stream(); error.onError(new Exception("private"));
        assertEquals(0, error.first.getCount()); assertFalse(error.hasOutput());
        SpikeInstrumentation.Stream visible = new SpikeInstrumentation.Stream(); visible.onMessage(visible("Lantern"));
        assertTrue(visible.hasOutput()); assertEquals(1, visible.done.getCount());
    }
    @Test public void callbackActivityIsDistinctFromBufferedTextAndNativeTokenCounters() {
        SpikeInstrumentation.Stream stream = new SpikeInstrumentation.Stream();
        assertNull(stream.observation(null, false, null, null));
        stream.onMessage(visible(""));
        stream.onMessage(new Message(Role.MODEL, Contents.Companion.of("private-thought"), Collections.emptyList(), Collections.singletonMap("thought", "hidden")));
        assertFalse(stream.hasOutput()); stream.onDone();
        RoleObservation observation = stream.observation(null, true, 0, 0);
        assertEquals(2, observation.callbackMessages); assertEquals(0, observation.bufferedTextBytes);
        assertEquals("unsupported_output", observation.callbackError);
        assertEquals(Integer.valueOf(0), observation.inputTokens);
        assertFalse(observation.toJson().toString().contains("private-thought"));
    }
    @Test public void mixedRejectedCallbackAndBufferedTextNeverImpliesAValidAnswer() {
        SpikeInstrumentation.Stream stream = new SpikeInstrumentation.Stream();
        stream.onMessage(new Message(Role.MODEL, Contents.Companion.of("hidden"), Collections.emptyList(), Collections.singletonMap("thought", "hidden")));
        stream.onMessage(visible("é")); stream.onDone();
        RoleObservation observation = stream.observation(null, false, null, null);
        assertTrue(stream.hasOutput()); assertEquals(2, observation.bufferedTextBytes);
        assertEquals("unsupported_output", observation.callbackError);
        assertThrows(Exception.class, stream::text);
    }
    @Test public void bufferedThinkingTagsAreObservationsNotValidation() {
        SpikeInstrumentation.Stream stream = new SpikeInstrumentation.Stream();
        stream.onMessage(visible("<think>")); stream.onDone();
        assertTrue(stream.hasOutput()); assertEquals(7, stream.observation(null, false, null, null).bufferedTextBytes);
        assertEquals("unsupported_output", assertThrows(Exception.class, stream::text).getMessage());
    }
    @Test public void terminalSnapshotIsFrozenAndLateCallbacksCannotChangeIt() {
        SpikeInstrumentation.Stream stream = new SpikeInstrumentation.Stream();
        stream.onMessage(visible("a")); stream.onDone();
        RoleObservation first = stream.observation(null, false, null, null);
        stream.onMessage(visible("late-private")); stream.onError(new RuntimeException("private error"));
        assertEquals(1, first.callbackMessages); assertEquals(1, first.bufferedTextBytes);
        assertEquals("none", first.callbackError);
        assertFalse(first.toJson().toString().contains("private"));
    }
}
