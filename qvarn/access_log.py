import datetime
import re

import jwt

import qvarn


QVARN_ID_RE = re.compile(r'([0-9a-f]{4}-[0-9a-f]{32}-[0-9a-f]{8})')


class AccessLogger(object):

    def __init__(self, entry_chunk_size=None):
        self.entry_chunk_size = entry_chunk_size or 300

    def log_access(self, request, response, data):
        rtype = self._get_rtype(request, data)
        op = self._get_op(request)

        ids, revision = self._get_ids_and_revision(request, data)
        if not ids:
            # we might be returning response that doesn't look like
            # a resource or a resource list (/version is one example)
            # can't do anything about it here.
            return

        ahead = request.get_header('Authorization', '')
        qhead = request.get_header('Qvarn-Token', '')
        ohead = request.get_header('Qvarn-Access-By', '')
        whead = request.get_header('Qvarn-Why', None)

        token_headers = ahead
        if qhead:
            token_headers = ', '.join([ahead, qhead])
        encoded_tokens = re.split(r'(?:\A|,\s*)Bearer ', token_headers)[1:]
        tokens = [jwt.decode(t, verify=False) for t in encoded_tokens]

        persons = [
            {
                'accessor_id': t['sub'],
                'accessor_type': 'person',
            }
            for t in tokens]
        clients = [
            {
                'accessor_id': t['aud'],
                'accessor_type': 'client',
            }
            for t in tokens]
        orgs = [
            {
                'accessor_id': t,
                'accessor_type': 'org',
            }
            for t in re.findall(r',?\s*Org (.+?)(?:,|\Z)', ohead) if t]
        others = [
            {
                'accessor_id': t,
                'accessor_type': 'other',
            }
            for t in re.findall(r',?\s*Other (.+?)(?:,|\Z)', ohead) if t]

        ip_address = request.headers.get('X-Forwarded-For')

        for some_ids in self._split(self.entry_chunk_size, ids):
            entry = {
                'type': 'access',
                'resource_type': rtype,
                'resource_ids': some_ids,
                'resource_revision': revision,
                'operation': op,
                'accessors': persons + clients + orgs + others,
                'why': whead,
                'ip_address': ip_address,
                'timestamp': datetime.datetime.utcnow().isoformat(),
            }
            qvarn.log.log('access_log', entry=entry)

    def _get_ids_and_revision(self, request, data):
        if not data or not isinstance(data, dict):
            # In case we are returning a file or it's a delete request
            # extract ID from path
            path_parts = request.path.split('/')
            if len(path_parts) > 2 and QVARN_ID_RE.match(path_parts[2]):
                ids = [path_parts[2]]
            else:
                ids = []
            revision = None
        else:
            if'resources' in data:
                ids = [r['id'] for r in data['resources']]
                revision = None
            elif 'id' in data:
                ids = [data['id']]
                revision = data.get('revision')
            else:
                ids, revision = [], None
        return ids, revision

    def _get_rtype(self, request, data):
        # If data has `resource_type` field, we use it as resource type
        if isinstance(data, dict) and 'resource_type' in data:
            return data['resource_type']

        # Othewise we try to guess it from request URL.
        path_parts = request.path.split('/')
        if len(path_parts) >= 2:
            rpart = path_parts[1]
            return rpart[:-1] if rpart[-1] == 's' else rpart

    def _get_op(self, request):
        if request.method == 'GET':
            path_parts = request.path.split('/')
            if len(path_parts) == 2:
                return 'LIST'
            elif 'search' in path_parts:
                return 'SEARCH'
            else:
                return 'GET'
        else:
            return request.method

    def _split(self, n, ids):
        while len(ids) > n:
            yield ids[:n]
            ids = ids[n:]
        yield ids
