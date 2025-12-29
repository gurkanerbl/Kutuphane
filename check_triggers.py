# trigger kontrol
from app import app, db

with app.app_context():
    triggers = db.session.execute(db.text(
        "SELECT trigger_name FROM information_schema.triggers WHERE trigger_schema = 'public'"
    )).fetchall()
    
    print("=== MEVCUT TRIGGER'LAR ===")
    if triggers:
        for t in triggers:
            print(f"  - {t[0]}")
    else:
        print("  (Hiç trigger yok)")
    
    # func kontrol
    functions = db.session.execute(db.text(
        "SELECT routine_name FROM information_schema.routines WHERE routine_type = 'FUNCTION' AND routine_schema = 'public'"
    )).fetchall()
    
    print("\n=== MEVCUT FUNCTION'LAR ===")
    if functions:
        for f in functions:
            print(f"  - {f[0]}")
    else:
        print("  (Hiç function yok)")
