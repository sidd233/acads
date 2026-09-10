def test_env_default_or_override(env):
    assert env in {"dev", "staging", "prod"}


def test_env_is_a_string(env):
    assert isinstance(env, str)
