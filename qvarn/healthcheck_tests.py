def test_healthcheck(Qvarn):
    qvarn = Qvarn()
    resp = qvarn.get('/healthcheck')
    assert resp.status_code == 200
    assert resp.json == {'message': 'healthy', 'status': 'OK'}
