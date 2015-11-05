# write_only.py - write only interface to databases
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


import unifiedapi


class WriteOnlyStorage(object):

    '''Write-only interface to a database.

    You MUST call ``set_db`` and ``set_item_prototype`` before doing
    anything else.

    '''

    def __init__(self):
        self._db = None
        self._item_type = None
        self._prototype = None
        self._subitem_prototypes = unifiedapi.SubItemPrototypes()
        self._id_generator = unifiedapi.ResourceIdGenerator()
        self._revision_id_type = 'revision id'

    def set_db(self, db):
        '''Set the database instance being used.'''
        self._db = db

    def set_item_prototype(self, item_type, prototype):
        '''Set type and prototype for items handled by this instance.'''
        self._item_type = item_type
        self._prototype = prototype

    def set_subitem_prototype(self, item_type, subitem_name, prototype):
        '''Set prototype for a subitem.'''
        self._subitem_prototypes.add(item_type, subitem_name, prototype)

    def add_item(self, item):
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

        with self._db:
            self._insert_item_into_database(added)
            for subitem_name, prototype in self._subitem_prototypes.get_all():
                self._insert_subitem_into_database(
                    added[u'id'], subitem_name, prototype)
        return added

    def _insert_item_into_database(self, item):
        ww = WriteWalker(self._db, self._item_type, item[u'id'])
        self._delete_item_in_transaction(item[u'id'], delete_subitems=False)
        ww.walk_item(item, self._prototype)

    def _insert_subitem_into_database(self, item_id, subitem_name, subitem):
        prototype = self._subitem_prototypes.get(self._item_type, subitem_name)
        table_name = u'%s_%s' % (self._item_type, subitem_name)
        ww = WriteWalker(self._db, table_name, item_id)
        self._delete_subitem_in_transaction(item_id, subitem_name)
        ww.walk_item(subitem, prototype)

    def update_item(self, item):
        '''Update an existing item.

        The item MUST have an id set.

        '''

        with self._db:
            current = self._get_current_revision(item[u'id'])
            if current != item[u'revision']:
                raise unifiedapi.WrongRevision(
                    item_id=item[u'id'],
                    current=current,
                    update=item[u'revision'])

            updated = item.copy()
            updated[u'revision'] = self._id_generator.new_id(
                self._revision_id_type)
            self._insert_item_into_database(updated)
        return updated

    def _get_current_revision(self, item_id):
        table_name = self._item_type
        column_names = [u'revision']
        match_columns = {u'id': item_id}
        rows = self._db.select_matching_rows(
            table_name, column_names, match_columns)
        for row in rows:
            return row[u'revision']

    def update_subitem(self, item_id, revision, subitem_name, subitem):
        with self._db:
            item = self._get_item(item_id)
            if item[u'revision'] != revision:
                raise unifiedapi.WrongRevision(
                    item_id=item_id,
                    current=item[u'revision'],
                    update=revision)
            updated = item.copy()
            updated[u'revision'] = self._id_generator.new_id(
                self._revision_id_type)
            self._insert_item_into_database(updated)
            self._insert_subitem_into_database(item_id, subitem_name, subitem)
            return updated[u'revision']

    def _get_item(self, item_id):
        ro = unifiedapi.ReadOnlyStorage()
        ro.set_db(self._db)
        ro.set_item_prototype(self._item_type, self._prototype)
        for subitem_name, prototype in self._subitem_prototypes.get_all():
            ro.set_subitem_prototype(self._item_type, subitem_name, prototype)
        return ro.get_item(item_id)

    def delete_item(self, item_id):
        '''Delete an item given its id.'''
        with self._db:
            self._delete_item_in_transaction(item_id)

    def _delete_item_in_transaction(self, item_id, delete_subitems=True):
        dw = DeleteWalker(self._db, self._item_type, item_id)
        dw.walk_item(self._prototype, self._prototype)
        if delete_subitems:
            for subitem_name, _ in self._subitem_prototypes.get_all():
                self._delete_subitem_in_transaction(item_id, subitem_name)

    def _delete_subitem_in_transaction(self, item_id, subitem_name):
        table_name = u'%s_%s' % (self._item_type, subitem_name)
        prototype = self._subitem_prototypes.get(self._item_type, subitem_name)
        dw = DeleteWalker(self._db, table_name, item_id)
        dw.walk_item(prototype, prototype)


class CannotAddWithId(unifiedapi.BadRequest):

    msg = u"Object being added already has an id"


class CannotAddWithRevision(unifiedapi.BadRequest):

    msg = u"Object being added already has a revision"


class WrongRevision(unifiedapi.Conflict):

    msg = "Update revision does not match the revision of object being updated"


class WriteWalker(unifiedapi.ItemWalker):

    '''Visit every part of an item to write it to database.'''

    def __init__(self, db, item_type, item_id):
        self._db = db
        self._item_type = item_type
        self._item_id = item_id

    def visit_main_dict(self, item, column_names):
        columns = [(x, item[x]) for x in column_names]
        if u'id' not in column_names:
            columns.append((u'id', self._item_id))
        self._db.insert(self._item_type, *columns)

    def visit_main_str_list(self, item, field):
        table_name = self._db.make_table_name(self._item_type, field)
        self._insert_str_list(table_name, field, self._item_id, None,
                              item[field])

    def _insert_str_list(self, table_name, column_name, item_id, dict_list_pos,
                         strings):
        prefix = [(u'id', item_id)]
        if dict_list_pos is not None:
            prefix.append((u'dict_list_pos', dict_list_pos))
        for i, str_value in enumerate(strings):
            columns = prefix + [
                (u'list_pos', i),
                (column_name, str_value),
            ]
            self._db.insert(table_name, *columns)

    def visit_dict_in_list(self, item, field, pos, column_names):
        table_name = self._db.make_table_name(self._item_type, field)
        some_dict = item[field][pos]
        columns = [
            (u'id', self._item_id),
            (u'list_pos', pos),
            ]
        columns += [(x, some_dict[x]) for x in column_names]
        self._db.insert(table_name, *columns)

    def visit_dict_in_list_str_list(self, item, field, pos, str_list_field):
        table_name = self._db.make_table_name(
            self._item_type, field, str_list_field)
        strings = item[field][pos][str_list_field]
        self._insert_str_list(table_name, str_list_field, self._item_id,
                              pos, strings)


class DeleteWalker(unifiedapi.ItemWalker):

    '''Visit every part of an item when deleting it.'''

    def __init__(self, db, item_type, item_id):
        self._db = db
        self._item_type = item_type
        self._item_id = item_id

    def visit_main_dict(self, item, column_names):
        self._delete_rows(self._item_type, self._item_id)

    def _delete_rows(self, table_name, item_id):
        self._db.delete_matching_rows(table_name, {u'id': item_id})

    def visit_main_str_list(self, item, field):
        table_name = self._db.make_table_name(self._item_type, field)
        self._delete_rows(table_name, self._item_id)

    def visit_main_dict_list(self, item, field, column_names):
        table_name = self._db.make_table_name(self._item_type, field)
        self._delete_rows(table_name, self._item_id)

    def visit_dict_in_list_str_list(self, item, field, pos, str_list_field):
        table_name = self._db.make_table_name(
            self._item_type, field, str_list_field)
        self._delete_rows(table_name, self._item_id)
