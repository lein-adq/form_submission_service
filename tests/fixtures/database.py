"""Database utilities for testing."""

from sqlalchemy import text
from sqlalchemy.orm import Session


def clear_table(db: Session, table_name: str) -> None:
    """Clear all data from a table."""
    db.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
    db.commit()


def verify_rls_context(db: Session) -> dict:
    """Verify that RLS context variables are set correctly."""
    user_id_result = db.execute(
        text("SELECT current_setting('app.user_id', true)")
    ).scalar()
    workspace_id_result = db.execute(
        text("SELECT current_setting('app.workspace_id', true)")
    ).scalar()

    return {
        "user_id": user_id_result,
        "workspace_id": workspace_id_result,
    }
