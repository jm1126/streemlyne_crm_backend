from sqlalchemy import create_engine

connections = [
    ("Direct Connection", "postgresql://postgres:lU7ylWeVOOUX9TSY@db.mcexfcjowunsmtilvepc.supabase.co:5432/postgres"),
    ("Session Pooler (aws-1)", "postgresql://postgres.mcexfcjowunsmtilvepc:lU7ylWeVOOUX9TSY@aws-1-eu-west-1.pooler.supabase.com:5432/postgres"),
    ("Transaction Pooler", "postgresql://postgres:lU7ylWeVOOUX9TSY@db.mcexfcjowunsmtilvepc.supabase.co:6543/postgres"),
]

for name, url in connections:
    print(f"\nTesting {name}...")
    try:
        engine = create_engine(url)
        conn = engine.connect()
        print(f"✅ {name} WORKS!")
        print(f"\nUse this in .env:\nDATABASE_URL={url}\n")
        conn.close()
        break
    except Exception as e:
        print(f"❌ {name} failed: {str(e)[:150]}")