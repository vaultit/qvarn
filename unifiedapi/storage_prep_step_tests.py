# storage_prep_step_tests.py - unit tests for StoragePreparationStep
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


import unittest

import unifiedapi


class StoragePreparationStepTests(unittest.TestCase):

    def test_raises_not_implemented_error_when_run(self):
        step = unifiedapi.StoragePreparationStep()
        with self.assertRaises(NotImplementedError):
            step.run(None)
