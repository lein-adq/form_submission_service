from sqlalchemy import text


def apply_rls_context(db, *, user_id, workspace_id=None):
    """
    Set RLS context variables on the database session.

    Uses SET LOCAL to scope variables to the current transaction,
    ensuring they persist for all queries in the same transaction
    and are automatically cleared when the transaction ends.

    Note: SET LOCAL requires an active transaction. SQLAlchemy with
    autocommit=False automatically starts a transaction, but we ensure
    one exists by beginning explicitly if needed.
    """
    # Ensure we're in a transaction (SET LOCAL requires this)
    # SQLAlchemy with autocommit=False automatically starts a transaction
    # on first query, but SET LOCAL must be in a transaction, so we begin
    # explicitly. This is safe even if a transaction already exists.
    try:
        db.begin()
    except Exception:
        # Transaction already exists, which is fine
        pass

    db.execute(text("SET LOCAL app.user_id = :uid"), {"uid": str(user_id)})
    if workspace_id:
        db.execute(
            text("SET LOCAL app.workspace_id = :wid"),
            {"wid": str(workspace_id)},
        )
