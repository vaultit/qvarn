import os

import pytest
import psycopg2

import qvarn
from qvarn.testing import TestApp
from qvarn.testing import DatabaseConnection
from qvarn.testing import create_qvarn_test_app
from qvarn.testing import get_jwt_token


def _get_qvarn_config():
    return {
        'database.type': 'postgres',
        'database.host': os.environ.get('QVARN_TEST_DB_HOST', 'localhost'),
        'database.port': os.environ.get('QVARN_TEST_DB_PORT', 5432),
        'database.name': os.environ.get('QVARN_TEST_DB_NAME', 'qvarn_tests'),
        'database.user': os.environ.get('QVARN_TEST_DB_USER', 'qvarn'),
        'database.password': os.environ.get('QVARN_TEST_DB_PASSWORD', 'qvarn'),
    }


@pytest.fixture(scope='session')
def Qvarn(postgres):
    config = _get_qvarn_config()

    qvarn, key, issuer = create_qvarn_test_app(config)

    def factory(scopes=None):
        app = TestApp(qvarn)
        if scopes:
            token = get_jwt_token(key, issuer, scopes)
            app.authorization = ('Bearer', token.decode())
        return app

    return factory


@pytest.fixture(scope='session')
def postgres():
    config = _get_qvarn_config()

    # Check if database connection.
    try:
        conn = psycopg2.connect(host=config['database.host'],
                                port=config['database.port'],
                                dbname=config['database.name'],
                                user=config['database.user'],
                                password=config['database.password'])
    except psycopg2.OperationalError as e:
        if os.environ.get('QVARN_TEST_DB_REQUIRED'):
            raise
        pytest.skip(str(e))
    else:
        conn.close()


@pytest.fixture()
def dbconn(postgres):
    config = _get_qvarn_config()
    sql = qvarn.PostgresAdapter(
        host=config['database.host'],
        port=config['database.port'],
        db_name=config['database.name'],
        user=config['database.user'],
        password=config['database.password'],
        min_conn=1,
        max_conn=5,
    )
    dbconn = DatabaseConnection()
    dbconn.set_sql(sql)
    return dbconn
