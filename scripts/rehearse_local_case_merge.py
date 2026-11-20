"""Rehearse case consolidation on private SQLite snapshots, never live stores."""
import argparse
import sqlite3
from contextlib import closing
from pathlib import Path


def connect_readonly(path):
    return sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)


def tables(db):
    return {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def rehearsal(workspace):
    destination = workspace / "merged-rehearsal.db"
    with destination.open("xb"):
        pass
    with closing(sqlite3.connect(destination)) as target:
        with closing(connect_readonly(workspace / "git-publish-app-1.db")) as standard:
            standard.backup(target)
        target.execute("PRAGMA foreign_keys=ON")
        target.row_factory = sqlite3.Row
        imports = (
            "cases", "images", "case_access", "analysis_runs", "analysis_events",
            "analysis_jobs", "clinical_reviews", "case_comments", "volume_analyses",
            "task_inference_runs", "stenosis_measurements", "research_reports",
            "report_revisions", "notifications", "notification_dismissals", "audit_events",
        )
        with target:
            target.execute("BEGIN")
            target.execute("PRAGMA defer_foreign_keys=ON")
            for filename in ("restored.db", "corovision-demo-app-1.db"):
                with closing(connect_readonly(workspace / filename)) as source:
                    source.row_factory = sqlite3.Row
                    known = {r["email"].casefold(): r for r in target.execute("SELECT * FROM users")}
                    user_map = {}
                    for user in source.execute("SELECT * FROM users"):
                        match = known.get(user["email"].casefold())
                        if match:
                            if (match["role"], match["status"]) != (user["role"], user["status"]):
                                raise ValueError(f"Account role/status conflict in {filename}")
                            user_map[user["id"]] = match["id"]
                        else:
                            insert(target, "users", dict(user))
                            user_map[user["id"]] = user["id"]

                    for table in imports:
                        if table not in tables(source):
                            continue
                        user_columns = {r[3] for r in target.execute(f'PRAGMA foreign_key_list("{table}")') if r[2] == "users"}
                        count = 0
                        for row in source.execute(f'SELECT * FROM "{table}"'):
                            values = dict(row)
                            for column in user_columns:
                                if values.get(column) is not None:
                                    values[column] = user_map[values[column]]
                            insert(target, table, values)
                            count += 1
                        if count:
                            print(filename, table, count)
            if target.execute("PRAGMA foreign_key_check").fetchone():
                raise ValueError("Foreign-key reconciliation failed")
        if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("Merged SQLite integrity check failed")
    print("Database rows rehearsed. Artifact paths and sign-in are not verified by this script.")


def insert(db, table, values):
    valid = {row[1] for row in db.execute(f'PRAGMA table_info("{table}")')}
    if missing := values.keys() - valid:
        raise ValueError(f"Destination schema lacks {table} fields: {sorted(missing)}")
    columns = ", ".join(f'"{column}"' for column in values)
    placeholders = ", ".join("?" for _ in values)
    db.execute(f'INSERT INTO "{table}" ({columns}) VALUES ({placeholders})', tuple(values.values()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    rehearsal(parser.parse_args().workspace)
