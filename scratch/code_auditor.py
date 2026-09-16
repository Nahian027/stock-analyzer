import sys
import os
import ast
import inspect
import sqlite3
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def audit_ast(filepath):
    """Parses AST to check syntax, function counts, classes, imports, and potential syntax/logic smells."""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        source = f.read()
    
    tree = ast.parse(source, filename=filepath)
    
    functions = []
    classes = []
    imports = []
    bare_excepts = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append(node.name)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                for n in node.names:
                    imports.append(n.name)
            else:
                imports.append(node.module or "")
        elif isinstance(node, ast.ExceptHandler):
            if node.type is None:
                bare_excepts.append(node.lineno)
                
    return {
        "filepath": filepath,
        "line_count": len(source.splitlines()),
        "byte_count": len(source.encode('utf-8')),
        "function_count": len(functions),
        "class_count": len(classes),
        "bare_excepts": bare_excepts,
        "functions": functions[:15]
    }

def audit_database(db_path):
    """Audits SQLite database schema, integrity, table sizes, and corruption checks."""
    if not os.path.exists(db_path):
        return {"status": "NOT_FOUND"}
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Check integrity
    cur.execute("PRAGMA integrity_check;")
    integrity = cur.fetchall()
    
    # Get tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cur.fetchall()]
    
    table_stats = {}
    for t in tables:
        try:
            cur.execute(f"SELECT count(*) FROM {t};")
            cnt = cur.fetchone()[0]
            table_stats[t] = cnt
        except Exception as e:
            table_stats[t] = f"Error: {e}"
            
    conn.close()
    
    return {
        "status": "OK",
        "size_mb": round(os.path.getsize(db_path) / (1024 * 1024), 2),
        "integrity": integrity,
        "tables": table_stats
    }

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    py_files = [
        os.path.join(root_dir, "app.py"),
        os.path.join(root_dir, "core_engine.py"),
        os.path.join(root_dir, "volume_agent.py"),
        os.path.join(root_dir, "stocknow_agent.py"),
        os.path.join(root_dir, "screener.py")
    ]
    
    print("=" * 80)
    print("CODEBASE COMPREHENSIVE STATIC & STRUCTURAL AUDIT REPORT")
    print("=" * 80)
    
    for pf in py_files:
        if os.path.exists(pf):
            res = audit_ast(pf)
            print(f"\n[FILE AUDIT] {os.path.basename(pf)}")
            print(f"  • Total Lines: {res['line_count']:,} lines | Size: {res['byte_count']/1024:.1f} KB")
            print(f"  • Functions: {res['function_count']} declared | Classes: {res['class_count']}")
            print(f"  • Bare Excepts (Lineno): {res['bare_excepts'] if res['bare_excepts'] else 'None (Clean)'}")
            print(f"  • Sample Functions: {', '.join(res['functions'][:6])}...")
            
    db_path = os.path.join(root_dir, "dse_forecast_tracker.db")
    db_res = audit_database(db_path)
    print("\n" + "=" * 80)
    print(f"[DATABASE AUDIT] {os.path.basename(db_path)}")
    print(f"  • Status: {db_res['status']} | Size: {db_res.get('size_mb', 0)} MB")
    print(f"  • Integrity Check: {db_res.get('integrity', [])}")
    print(f"  • Table Row Counts: {db_res.get('tables', {})}")
    print("=" * 80)

if __name__ == "__main__":
    main()
