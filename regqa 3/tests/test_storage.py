from regqa.fetch.storage import content_hash, relative_path_for, store


def test_same_bytes_produce_the_same_path(tmp_path):
    first_digest, first_path = store(tmp_path, b"pdf bytes")
    second_digest, second_path = store(tmp_path, b"pdf bytes")
    assert first_digest == second_digest
    assert first_path == second_path
    assert len(list(tmp_path.rglob("*.pdf"))) == 1


def test_different_bytes_produce_different_paths(tmp_path):
    _, a = store(tmp_path, b"one")
    _, b = store(tmp_path, b"two")
    assert a != b


def test_path_is_sharded_by_hash_prefix():
    digest = content_hash(b"x")
    assert relative_path_for(digest).parts[0] == digest[:2]


def test_rewriting_does_not_touch_an_existing_file(tmp_path):
    _, relative = store(tmp_path, b"payload")
    absolute = tmp_path / relative
    before = absolute.stat().st_mtime_ns
    store(tmp_path, b"payload")
    assert absolute.stat().st_mtime_ns == before
