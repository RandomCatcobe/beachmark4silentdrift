import json, os
from sqlalchemy import create_engine, text
db = "sqlalchemy_autocommit_probe.sqlite"
if os.path.exists(db):
    os.unlink(db)
engine = create_engine("sqlite:///" + db)
with engine.connect() as conn:
    conn.execute(text("create table t (x int)"))
    conn.execute(text("insert into t (x) values (1)"))
with engine.connect() as conn:
    count = conn.execute(text("select count(*) from t")).scalar()
print(json.dumps({"count_after_reopen": count}, sort_keys=True))
