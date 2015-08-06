import unittest

import unifiedapi


class UtilTests(unittest.TestCase):

    def test_basic_route_to_scope(self):
        route_scope = unifiedapi.route_to_scope('/orgs', 'GET')
        self.assertEqual(route_scope, u'uapi_orgs_get')

    def test_basic_id_route_to_scope(self):
        route_scope = unifiedapi.route_to_scope('/orgs/<item_id>', 'PUT')
        self.assertEqual(route_scope, u'uapi_orgs_id_put')

    def test_basic_subitem_route_to_scope(self):
        route_scope = unifiedapi.route_to_scope(
            '/orgs/<item_id>/document', 'PUT')
        self.assertEqual(route_scope, u'uapi_orgs_id_document_put')

    def test_search_route_to_scope(self):
        route_scope = unifiedapi.route_to_scope(
            '/orgs/search/<search_criteria:path>', 'GET')
        self.assertEqual(route_scope, u'uapi_orgs_search_id_get')

    def test_listener_notification_route_to_scope(self):
        route_scope = unifiedapi.route_to_scope(
            '/orgs/listeners/<id>/notifications/<id>', 'DELETE')
        self.assertEqual(
            route_scope, u'uapi_orgs_listeners_id_notifications_id_delete')
