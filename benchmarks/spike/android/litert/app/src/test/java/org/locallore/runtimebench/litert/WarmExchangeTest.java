// Copyright 2026 LocalLore contributors.
// SPDX-License-Identifier: Apache-2.0
package org.locallore.runtimebench.litert;

import static org.junit.Assert.*;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Set;
import org.junit.Assume;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;

public class WarmExchangeTest {
    @Rule public TemporaryFolder files = new TemporaryFolder();
    private static final String TOKEN = "0123456789abcdef0123456789abcdef";
    private Path directory() { return files.getRoot().toPath().resolve("warm-" + TOKEN); }
    private WarmExchange create() throws Exception {
        Files.createDirectory(directory());
        Files.write(directory().resolve("owner-v1"), "locallore-warm-v1".getBytes(StandardCharsets.UTF_8));
        return new WarmExchange(files.getRoot(), TOKEN);
    }
    static byte[] request(String role) {
        return ("{\"version\":1,\"role\":\"" + role + "\",\"prompt\":\"original synthetic prompt\","
            + "\"max_tokens\":8,\"context_tokens\":4096,\"threads\":4,\"schema\":null}").getBytes(StandardCharsets.UTF_8);
    }
    private void write(String name, byte[] bytes) throws Exception { Files.write(directory().resolve(name), bytes); }
    private JsonObject result() { JsonObject result = new JsonObject(); result.addProperty("text", "synthetic private text"); return result; }

    @Test public void normalSequentialExchangeHasExactEnvelopeAndZeroOverwrite() throws Exception {
        WarmExchange exchange = create();
        assertNull(exchange.poll(1));
        write("request-1.json", request("director"));
        assertEquals("director", exchange.poll(1).role);
        exchange.publish(1, result());
        JsonObject envelope = JsonParser.parseString(new String(Files.readAllBytes(directory().resolve("result-1.json")), StandardCharsets.UTF_8)).getAsJsonObject();
        assertEquals(Set.of("version", "session", "step", "result"), envelope.keySet());
        assertEquals(TOKEN, envelope.get("session").getAsString());
        assertEquals(1, envelope.get("step").getAsInt());
        assertTrue(envelope.get("result").isJsonObject());
        write("request-2.json", request("narrator"));
        assertEquals("narrator", exchange.poll(2).role);
        exchange.publish(2, result());
        assertFalse(Files.exists(directory().resolve("result-2.json.partial")));
        assertThrows(IOException.class, () -> exchange.publish(2, result()));
        exchange.check();
    }
    @Test public void tokenCannotChoosePathOrAcceptUppercase() throws Exception {
        for (String token : new String[]{"../arbitrary", "0".repeat(31), "A".repeat(32), "0".repeat(33), ""})
            assertThrows(IOException.class, () -> new WarmExchange(files.getRoot(), token));
        assertThrows(IOException.class, () -> new WarmExchange(files.getRoot(), null));
    }
    @Test public void missingOrChangedMarkerRefusesOwnership() throws Exception {
        WarmExchange exchange = create();
        Files.write(directory().resolve("owner-v1"), "locallore-warm-v1\n".getBytes(StandardCharsets.UTF_8));
        assertThrows(IOException.class, exchange::check);
        Files.delete(directory().resolve("owner-v1"));
        assertThrows(IOException.class, exchange::check);
    }
    @Test public void wrongRoleIsNeverConsumed() throws Exception {
        WarmExchange exchange = create(); write("request-1.json", request("narrator"));
        assertThrows(IOException.class, () -> exchange.poll(1));
        assertFalse(Files.exists(directory().resolve("result-1.json")));
    }
    @Test public void earlyNarratorRefusedEvenDuringDirectorGeneration() throws Exception {
        WarmExchange exchange = create(); write("request-1.json", request("director"));
        exchange.poll(1); write("request-2.json", request("narrator"));
        assertThrows(IOException.class, exchange::check);
        assertThrows(IOException.class, () -> exchange.publish(1, result()));
    }
    @Test public void preexistingFinalCannotBeReplaced() throws Exception {
        WarmExchange exchange = create(); write("request-1.json", request("director")); exchange.poll(1);
        byte[] sentinel = "original final".getBytes(StandardCharsets.UTF_8); write("result-1.json", sentinel);
        assertThrows(IOException.class, () -> exchange.publish(1, result()));
        assertArrayEquals(sentinel, Files.readAllBytes(directory().resolve("result-1.json")));
    }
    @Test public void partialRequestIgnoredUntilFinalAndRepeatedConsumptionRefused() throws Exception {
        WarmExchange exchange = create(); write("request-1.json.partial", request("director"));
        assertNull(exchange.poll(1));
        Files.move(directory().resolve("request-1.json.partial"), directory().resolve("request-1.json"));
        exchange.poll(1);
        assertThrows(IOException.class, () -> exchange.poll(1));
    }
    @Test public void changedConsumedRequestAndResultAreRejected() throws Exception {
        WarmExchange exchange = create(); write("request-1.json", request("director")); exchange.poll(1); exchange.publish(1, result());
        byte[] prior = Files.readAllBytes(directory().resolve("request-1.json"));
        write("request-1.json", request("narrator")); assertThrows(IOException.class, exchange::check);
        write("request-1.json", prior);
        write("result-1.json", "{}".getBytes(StandardCharsets.UTF_8)); assertThrows(IOException.class, exchange::check);
    }
    @Test public void oversizedMalformedDuplicateAndUnknownRequestsFailClosed() throws Exception {
        WarmExchange exchange = create();
        for (byte[] bytes : new byte[][]{new byte[32769], {(byte)0xff},
                new String(request("director"), StandardCharsets.UTF_8).replace("\"version\":1", "\"version\":1,\"version\":1").getBytes(StandardCharsets.UTF_8),
                new String(request("director"), StandardCharsets.UTF_8).replace("\"version\":1", "\"unknown\":1,\"version\":1").getBytes(StandardCharsets.UTF_8)}) {
            write("request-1.json", bytes); assertThrows(IOException.class, () -> exchange.poll(1));
        }
    }
    @Test public void emptyCancelRecognizedButMalformedCancelRefused() throws Exception {
        WarmExchange exchange = create(); assertFalse(exchange.cancelled());
        write("cancel.partial", new byte[0]); assertFalse(exchange.cancelled());
        Files.delete(directory().resolve("cancel.partial"));
        write("cancel", new byte[0]); assertTrue(exchange.cancelled());
        write("cancel", new byte[]{1}); assertThrows(IOException.class, exchange::cancelled);
    }
    @Test public void earlyForeignResultCannotAppearDuringGeneration() throws Exception {
        WarmExchange exchange = create(); write("request-1.json", request("director")); exchange.poll(1);
        write("result-2.json", "{}".getBytes(StandardCharsets.UTF_8));
        assertThrows(IOException.class, exchange::check);
    }
    @Test public void unknownFilesAndDirectoriesRefused() throws Exception {
        WarmExchange exchange = create(); write("unowned", new byte[0]);
        assertThrows(IOException.class, exchange::check);
        Files.delete(directory().resolve("unowned")); Files.createDirectory(directory().resolve("request-1.json"));
        assertThrows(IOException.class, exchange::check);
    }
    @Test public void symlinkMarkerAndSessionRefused() throws Exception {
        WarmExchange exchange = create();
        Path original = files.getRoot().toPath().resolve("original-marker");
        Files.move(directory().resolve("owner-v1"), original);
        try { Files.createSymbolicLink(directory().resolve("owner-v1"), original); }
        catch (IOException | UnsupportedOperationException failure) { Assume.assumeNoException("Host cannot create symbolic links", failure); }
        assertThrows(IOException.class, exchange::check);
        Files.delete(directory().resolve("owner-v1")); Files.move(original, directory().resolve("owner-v1"));
        Path moved = files.getRoot().toPath().resolve("other"); Files.move(directory(), moved);
        Files.createSymbolicLink(directory(), moved);
        assertThrows(IOException.class, () -> new WarmExchange(files.getRoot(), TOKEN));
    }
}
