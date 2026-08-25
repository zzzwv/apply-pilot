from app.core.security import create_access_token, hash_password, verify_password


def test_password_hash_round_trip_rejects_a_wrong_password() -> None:
    """Catches credentials being stored or accepted without a verifiable password hash."""
    password_hash = hash_password("correct horse battery staple")

    assert password_hash != "correct horse battery staple"
    assert verify_password("correct horse battery staple", password_hash)
    assert not verify_password("wrong password", password_hash)


def test_access_token_contains_the_subject() -> None:
    """Catches access tokens that cannot identify the authenticated user."""
    token = create_access_token("user-id")

    assert token.count(".") == 2
