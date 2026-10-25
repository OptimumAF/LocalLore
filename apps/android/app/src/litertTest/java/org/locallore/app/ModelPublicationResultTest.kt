/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import org.junit.Assert.*
import org.junit.Test

/** Pure closed-result tests. No JNI publisher reference, library load, filesystem or device. */
class ModelPublicationResultTest {
    @Test fun nativeWireCodesRetainTheirExactCategories() {
        assertEquals(ModelPublicationResult.PUBLISHED, ModelPublicationResult.fromWire(0))
        assertEquals(ModelPublicationResult.DESTINATION_EXISTS, ModelPublicationResult.fromWire(1))
        assertEquals(ModelPublicationResult.UNSUPPORTED, ModelPublicationResult.fromWire(2))
        assertEquals(ModelPublicationResult.IO_FAILURE, ModelPublicationResult.fromWire(3))
        assertEquals(ModelPublicationResult.INVALID_INPUT, ModelPublicationResult.fromWire(4))
        assertEquals(ModelPublicationResult.SYMBOL_UNAVAILABLE, ModelPublicationResult.fromWire(5))
        assertEquals(ModelPublicationResult.RENAME_INVALID, ModelPublicationResult.fromWire(6))
        assertEquals(ModelPublicationResult.RENAME_UNAVAILABLE, ModelPublicationResult.fromWire(7))
        assertEquals(ModelPublicationResult.RENAME_UNSUPPORTED, ModelPublicationResult.fromWire(8))
    }

    @Test fun unknownWireCodesIncludingIntegerExtremesRemainUnknown() {
        listOf(Int.MIN_VALUE, -65_536, -1, 9, 65_536, Int.MAX_VALUE).forEach { code ->
            assertEquals(ModelPublicationResult.UNKNOWN, ModelPublicationResult.fromWire(code))
            assertFailure(LocalModelFailure.STORAGE) { ModelPublicationResult.fromWire(code).requirePublished() }
        }
    }

    @Test fun successReturnsWithDefaultObserverAndNeverInventsFailure() {
        ModelPublicationResult.fromWire(0).requirePublished()
    }

    @Test fun allFailedCategoriesRetainExistingFixedUiMappingWithoutNativeDetails() {
        assertFailure(LocalModelFailure.UNSAFE_PATH) { ModelPublicationResult.fromWire(1).requirePublished() }
        assertFailure(LocalModelFailure.STORAGE) { ModelPublicationResult.fromWire(2).requirePublished() }
        assertFailure(LocalModelFailure.STORAGE) { ModelPublicationResult.fromWire(3).requirePublished() }
        assertFailure(LocalModelFailure.UNSAFE_PATH) { ModelPublicationResult.fromWire(4).requirePublished() }
        assertFailure(LocalModelFailure.STORAGE) { ModelPublicationResult.fromWire(5).requirePublished() }
        assertFailure(LocalModelFailure.STORAGE) { ModelPublicationResult.fromWire(6).requirePublished() }
        assertFailure(LocalModelFailure.STORAGE) { ModelPublicationResult.fromWire(7).requirePublished() }
        assertFailure(LocalModelFailure.STORAGE) { ModelPublicationResult.fromWire(8).requirePublished() }
        assertFailure(LocalModelFailure.STORAGE) { ModelPublicationResult.UNKNOWN.requirePublished() }
    }

    @Test fun observerSeesEveryClosedCategoryExactlyOnceBeforeReturnOrFailure() {
        val expectedFailures = mapOf(
            ModelPublicationResult.DESTINATION_EXISTS to LocalModelFailure.UNSAFE_PATH,
            ModelPublicationResult.UNSUPPORTED to LocalModelFailure.STORAGE,
            ModelPublicationResult.IO_FAILURE to LocalModelFailure.STORAGE,
            ModelPublicationResult.INVALID_INPUT to LocalModelFailure.UNSAFE_PATH,
            ModelPublicationResult.SYMBOL_UNAVAILABLE to LocalModelFailure.STORAGE,
            ModelPublicationResult.RENAME_INVALID to LocalModelFailure.STORAGE,
            ModelPublicationResult.RENAME_UNAVAILABLE to LocalModelFailure.STORAGE,
            ModelPublicationResult.RENAME_UNSUPPORTED to LocalModelFailure.STORAGE,
            ModelPublicationResult.UNKNOWN to LocalModelFailure.STORAGE,
        )
        ModelPublicationResult.values().forEach { result ->
            val events = mutableListOf<String>()
            val observations = mutableListOf<ModelPublicationResult>()
            try {
                result.requirePublished { observed ->
                    observations += observed
                    events += "observed"
                }
                events += "returned"
                assertEquals(ModelPublicationResult.PUBLISHED, result)
            } catch (failure: LocalModelException) {
                events += "failed"
                assertEquals(expectedFailures[result], failure.failure)
            }
            assertEquals(listOf(result), observations)
            assertEquals(listOf("observed", if (result == ModelPublicationResult.PUBLISHED) "returned" else "failed"), events)
        }
    }

    private fun assertFailure(expected: LocalModelFailure, action: () -> Unit) {
        try {
            action()
            fail("Expected fixed publication failure")
        } catch (failure: LocalModelException) {
            assertEquals(expected, failure.failure)
            assertEquals("Local model unavailable: ${expected.name}", failure.message)
            assertNull(failure.cause)
        }
    }
}
