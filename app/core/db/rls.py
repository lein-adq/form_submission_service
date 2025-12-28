from sqlalchemy import text


def apply_rls_context(db, *, user_id, workspace_id=None):
    db.execute(
        text("select set_config('app.user_id', :uid, true)"), {"uid": str(user_id)}
    )
    if workspace_id:
        db.execute(
            text("select set_config('app.workspace_id', :wid, true)"),
            {"wid": str(workspace_id)},
        )
