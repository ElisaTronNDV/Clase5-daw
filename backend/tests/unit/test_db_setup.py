def test_users_table_created(initialized_db):
    from app.db.base import Base
    from app.models.user import User

    assert "users" in Base.metadata.tables
    table = User.__table__

    assert table.name == "users"

    columns = {column.name: column for column in table.columns}
    assert set(columns) == {"id", "email", "hashed_password", "created_at"}

    assert columns["id"].primary_key is True
    assert columns["id"].autoincrement in (True, "auto")

    assert columns["email"].type.length == 255
    assert columns["email"].unique is True
    assert columns["email"].nullable is False
    assert columns["email"].index is True

    assert columns["hashed_password"].type.length == 255
    assert columns["hashed_password"].nullable is False

    assert columns["created_at"].nullable is False
    assert columns["created_at"].default is not None
