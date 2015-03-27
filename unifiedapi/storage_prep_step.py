# storage_prep_step.py - base class for StoragePreprer steps
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


class StoragePreparationStep(object):

    '''A storage preparation step.

    Subclasses must define the ``run`` method.

    '''

    def run(self, db):
        raise NotImplementedError()
