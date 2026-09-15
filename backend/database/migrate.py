import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

def run_migration():
    db_path = os.path.abspath("codex.db")
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA table_info(conversations);")
        columns = [row[1] for row in cursor.fetchall()]

        if columns:
            if "github_repo_url" not in columns:
                cursor.execute("ALTER TABLE conversations ADD COLUMN github_repo_url VARCHAR(500);")
                logger.info("Added github_repo_url column to conversations table.")

            if "github_token" not in columns:
                cursor.execute("ALTER TABLE conversations ADD COLUMN github_token VARCHAR(500);")
                logger.info("Added github_token column to conversations table.")

            conn.commit()
    except Exception as e:
        logger.error(f"Migration error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()
