/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
package org.locallore.app

import androidx.compose.ui.test.junit4.createComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.runners.Suite

/**
 * Nested opt-in cohort is excluded from default scanner discovery. Its explicit
 * selector is org.locallore.app.CapacityLifecycleCohort$OrderedSuite.
 */
class CapacityLifecycleCohort {
    /** Ordinary empty Compose-rule lifecycle before any capacity native work. */
    @RunWith(AndroidJUnit4::class)
    class Before {
        @get:Rule val compose = createComposeRule()
        @Test fun emptyComposeBeforeCapacityWorkClosesNormally() {
            CapacityTestFixture.requireCapacityIdentity()
            compose.waitForIdle()
        }
    }

    /** Ordinary teardown remains observable after the native and gameplay UI cases. */
    @RunWith(AndroidJUnit4::class)
    class After {
        @get:Rule val compose = createComposeRule()
        @Test fun emptyComposeAfterCapacityWorkClosesNormally() {
            CapacityTestFixture.requireCapacityIdentity()
            compose.waitForIdle()
        }
    }

    /** One process: control, ordered native cases, gameplay UI case, control. */
    @RunWith(Suite::class)
    @Suite.SuiteClasses(
        Before::class,
        SqliteCapacityNativeTest::class,
        SqliteCapacityInstrumentedTest::class,
        After::class,
    )
    class OrderedSuite
}
