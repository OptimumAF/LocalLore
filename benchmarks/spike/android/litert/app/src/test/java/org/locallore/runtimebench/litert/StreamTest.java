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
}
