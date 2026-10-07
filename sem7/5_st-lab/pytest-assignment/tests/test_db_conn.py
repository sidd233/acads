def test_connection_is_open(db_conn):
    assert db_conn.closed is False


def test_connection_reads_rows(db_conn):
    assert db_conn.get(1) == {"id": 1, "name": "Ada"}


def test_same_instance_across_module(db_conn, request):
    request.config._seen = getattr(request.config, "_seen", set())
    request.config._seen.add(id(db_conn))
    assert len(request.config._seen) == 1
