# storage_prep.py - prepare database schema, migrate to current schema
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


import logging

import unifiedapi


class StoragePreparer(object):

    '''Prepare a database for use.

    The database is prepared by running a sequence of steps. Each step
    can create or remove tables or columns, or insert or delete rows.
    As long as no step is ever dropped from the application, or
    materially altered, this should guarantee that the database is
    automatically migrated to the current schema.

    The list of steps that has been run already is kept in the
    database, in the ``migrations`` table. This avoids having the
    steps try to figure out if they need to do anything or not.

    '''

    def __init__(self, item_type):
        # Use double underscore so that automatically constructed
        # table names do not clash.
        self._migrations_table_name = unifiedapi.table_name(
            resource_type=item_type, auxtable=u'migrations')

        self._mandatory_steps = [
            (u'prepare-migrations-table',
             PrepareMigrationsTable(self._migrations_table_name)),
        ]
        self._steps = []

    def set_mandatory_steps(self, steps):
        '''Set the mandatory set of steps that are always run.

        This is only for the use of unit tests.

        '''

        self._mandatory_steps = steps

    @property
    def step_names(self):
        '''List of steps names that have been added.

        This is only for the use of unit tests.

        '''

        return [x[0] for x in self._steps]

    def add_step(self, name, step):
        '''Add a step.'''
        if (name, step) in self._steps:
            raise DuplicateStepName(name=name)
        self._steps.append((name, step))

    def run(self, db):
        '''Run all steps.'''
        self._run_mandatory_steps(db)
        if self._steps:
            self._run_steps(db)

    def _run_mandatory_steps(self, db):
        for name, step in self._mandatory_steps:
            self._run_step(db, name, step)

    def _run_steps(self, db):
        done_steps = self._get_done_steps(db)
        for name, step in self._steps:
            if name not in done_steps:
                self._run_step(db, name, step)
                self._remember_step_name(db, name)

    def _get_done_steps(self, db):
        return [
            row['name']
            for row in db.select(self._migrations_table_name, [u'name'])]

    def _run_step(self, db, name, step):
        logging.info('Running storage preparation step %s', name)
        if hasattr(step, 'run'):
            step.run(db)
        else:
            step(db)

    def _remember_step_name(self, db, name):
        db.insert(self._migrations_table_name, (u'name', name))


class PrepareMigrationsTable(unifiedapi.StoragePreparationStep):

    def __init__(self, table_name):
        self._table_name = table_name

    def run(self, db):
        db.create_table(self._table_name, (u'name', unicode))


class DuplicateStepName(unifiedapi.BackendException):

    msg = u'Duplicate storage preparation step name: {name}'
