# write_only.py - write only interface to databases
#
# Copyright 2015, 2016 Suomen Tilaajavastuu Oy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import qvarn


class WriteOnlyStorage(object):

    '''Write-only interface to a database.

    You MUST call ``set_item_prototype`` before doing anything else.

    '''

    def __init__(self):
        self._item_type = None
        self._prototype = None
        self._subitem_prototypes = qvarn.SubItemPrototypes()
        self._id_generator = qvarn.ResourceIdGenerator()
        self._revision_id_type = 'revision id'

    def set_item_prototype(self, item_type, prototype):
        '''Set type and prototype for items handled by this instance.'''
        self._item_type = item_type
        self._prototype = prototype

    def set_subitem_prototype(self, item_type, subitem_name, prototype):
        '''Set prototype for a subitem.'''
        self._subitem_prototypes.add(item_type, subitem_name, prototype)

    def add_item(self, transaction, item):
        '''Add an item to the database.

        The item MUST NOT have an id set yet. The id is set by this
        method. The modified item is returned by this method: the
        parameter is NOT modified in place.

        '''

        if u'id' in item:
            raise CannotAddWithId(id=item[u'id'])
        if u'revision' in item:
            raise CannotAddWithRevision(revision=item[u'revision'])

        added = dict(item)
        added[u'id'] = self._id_generator.new_id(self._item_type)
        added[u'revision'] = self._id_generator.new_id(self._revision_id_type)

        self._insert_item_into_database(transaction, added)
        for subitem_name, prototype in self._subitem_prototypes.get_all():
            self._insert_subitem_into_database(
                transaction, added[u'id'], subitem_name, prototype)
        return added

    def _insert_item_into_database(self, transaction, item):
        ww = WriteWalker(transaction, self._item_type, item[u'id'])
        ww.walk_item(item, self._prototype)

    def _insert_subitem_into_database(self, transaction, item_id,
                                      subitem_name, subitem):
        prototype = self._subitem_prototypes.get(self._item_type, subitem_name)
        table_name = qvarn.table_name(
            resource_type=self._item_type, subpath=subitem_name)
        ww = WriteWalker(transaction, table_name, item_id)
        ww.walk_item(subitem, prototype)

    def update_item(self, transaction, item):
        '''Update an existing item.

        The item MUST have an id set.

        '''

        current = self._get_current_revision(transaction, item[u'id'])
        if current != item[u'revision']:
            raise qvarn.WrongRevision(
                item_id=item[u'id'],
                current=current,
                update=item[u'revision'])

        updated = item.copy()
        updated[u'revision'] = self._id_generator.new_id(
            self._revision_id_type)

        self._delete_item_in_transaction(
            transaction, item[u'id'], delete_subitems=False)

        self._insert_item_into_database(transaction, updated)
        return updated

    def _get_current_revision(self, transaction, item_id):
        table_name = qvarn.table_name(resource_type=self._item_type)
        column_names = [u'revision']
        match_columns = ('=', table_name, u'id', item_id)
        rows = transaction.select(table_name, column_names, match_columns)
        for row in rows:
            return row[u'revision']

    def update_subitem(self, transaction, item_id, revision, subitem_name,
                       subitem):
        current_revision = self._get_current_revision(transaction, item_id)
        if current_revision != revision:
            raise qvarn.WrongRevision(
                item_id=item_id,
                current=current_revision,
                update=revision)

        # Update revision of main item.
        new_revision = self._id_generator.new_id(self._revision_id_type)
        self._update_revision(transaction, item_id, new_revision)

        # Add or replace subitem.
        self._delete_subitem_in_transaction(
            transaction, item_id, subitem_name)
        self._insert_subitem_into_database(
            transaction, item_id, subitem_name, subitem)

        return new_revision

    def _update_revision(self, transaction, item_id, new_revision):
        table_name = qvarn.table_name(resource_type=self._item_type)
        match_columns = ('=', table_name, u'id', item_id)
        values = {
            u'revision': new_revision,
        }
        transaction.update(table_name, match_columns, values)

    def delete_item(self, transaction, item_id):
        '''Delete an item given its id.'''
        self._delete_item_in_transaction(transaction, item_id)

    def _delete_item_in_transaction(self, transaction, item_id,
                                    delete_subitems=True):
        dw = DeleteWalker(transaction, self._item_type, item_id)
        dw.walk_item(self._prototype, self._prototype)
        if delete_subitems:
            for subitem_name, _ in self._subitem_prototypes.get_all():
                self._delete_subitem_in_transaction(
                    transaction, item_id, subitem_name)

    def _delete_subitem_in_transaction(self, transaction, item_id,
                                       subitem_name):
        table_name = qvarn.table_name(
            resource_type=self._item_type, subpath=subitem_name)
        prototype = self._subitem_prototypes.get(self._item_type, subitem_name)
        dw = DeleteWalker(transaction, table_name, item_id)
        dw.walk_item(prototype, prototype)


class CannotAddWithId(qvarn.BadRequest):

    msg = u"Object being added already has an id"


class CannotAddWithRevision(qvarn.BadRequest):

    msg = u"Object being added already has a revision"


class WrongRevision(qvarn.Conflict):

    msg = ('Updating resource {item_id} failed: '
           ' resource currently has revision {current}, '
           'update wants to update {update}')


class WriteWalker(qvarn.ItemWalker):

    '''Visit every part of an item to write it to database.'''

    def __init__(self, transaction, item_type, item_id):
        self._transaction = transaction
        self._item_type = item_type
        self._item_id = item_id

    def visit_main_dict(self, item, column_names):
        columns = dict((x, item[x]) for x in column_names)
        if u'id' not in column_names:
            columns[u'id'] = self._item_id
        self._transaction.insert(self._item_type, columns)

    def visit_main_str_list(self, item, field):
        table_name = qvarn.table_name(
            resource_type=self._item_type, list_field=field)
        self._insert_str_list(table_name, field, self._item_id, None,
                              item[field])

    def _insert_str_list(self, table_name, column_name, item_id, dict_list_pos,
                         strings):
        prefix = {
            u'id': item_id,
        }
        if dict_list_pos is not None:
            prefix[u'dict_list_pos'] = dict_list_pos
        for i, str_value in enumerate(strings):
            columns = dict(prefix)
            columns[u'list_pos'] = i
            columns[column_name] = str_value
            self._transaction.insert(table_name, columns)

    def visit_dict_in_list(self, item, field, pos, column_names):
        table_name = qvarn.table_name(
            resource_type=self._item_type, list_field=field)
        columns = {
            u'id': self._item_id,
            u'list_pos': pos,
        }
        for column_name in column_names:
            columns[column_name] = item[field][pos][column_name]
        self._transaction.insert(table_name, columns)

    def visit_dict_in_list_str_list(self, item, field, pos, str_list_field):
        table_name = qvarn.table_name(
            resource_type=self._item_type,
            list_field=field,
            subdict_list_field=str_list_field)
        strings = item[field][pos][str_list_field]
        self._insert_str_list(table_name, str_list_field, self._item_id,
                              pos, strings)

    def visit_dict_in_inner_list(self, item, field, outer_pos, inner_field,
                                 inner_pos, column_names):
        table_name = qvarn.table_name(
            resource_type=self._item_type,
            list_field=field,
            subdict_list_field=inner_field)
        columns = {
            u'id': self._item_id,
            u'dict_list_pos': outer_pos,
            u'list_pos': inner_pos,
        }
        inner_dict = item[field][outer_pos][inner_field][inner_pos]
        for column_name in column_names:
            columns[column_name] = inner_dict[column_name]
        self._transaction.insert(table_name, columns)


class DeleteWalker(qvarn.ItemWalker):

    '''Visit every part of an item when deleting it.'''

    def __init__(self, transaction, item_type, item_id):
        self._transaction = transaction
        self._item_type = item_type
        self._item_id = item_id

    def visit_main_dict(self, item, column_names):
        self._delete_rows(self._item_type, self._item_id)

    def _delete_rows(self, table_name, item_id):
        self._transaction.delete(table_name, ('=', table_name, u'id', item_id))

    def visit_main_str_list(self, item, field):
        table_name = qvarn.table_name(
            resource_type=self._item_type, list_field=field)
        self._delete_rows(table_name, self._item_id)

    def visit_main_dict_list(self, item, field, column_names):
        table_name = qvarn.table_name(
            resource_type=self._item_type, list_field=field)
        self._delete_rows(table_name, self._item_id)

    def visit_dict_in_list_str_list(self, item, field, pos, str_list_field):
        table_name = qvarn.table_name(
            resource_type=self._item_type,
            list_field=field,
            subdict_list_field=str_list_field)
        self._delete_rows(table_name, self._item_id)

    def visit_inner_dict_list(self, item, field, inner_field, column_names):
        table_name = qvarn.table_name(
            resource_type=self._item_type,
            list_field=field,
            subdict_list_field=inner_field)
        self._delete_rows(table_name, self._item_id)
