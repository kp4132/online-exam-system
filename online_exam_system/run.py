"""
One-Click Launcher for Online Exam & Quiz System
Starts Flask and automatically opens your web browser.
"""

import webbrowser
import threading
import time
from app import app, init_db, get_local_ip

PORT = 5001

def open_browser():
    time.sleep(1.5)
    url = f"http://127.0.0.1:{PORT}"
    print("\n" + "="*60)
    print(f"🚀 Browser me website kholi ja rahi hai: {url}")
    print("="*60 + "\n")
    webbrowser.open(url)

if __name__ == '__main__':
    init_db()
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.jinja_env.auto_reload = True
    local_ip = get_local_ip()
    threading.Thread(target=open_browser, daemon=True).start()
    
    print("\n" + "="*60)
    print("🎓 ONLINE EXAM & QUIZ SYSTEM START HO GAYA HAI!")
    print(f"👉 PC Website URL: http://127.0.0.1:{PORT}")
    print(f"👉 Mobile URL:     http://{local_ip}:{PORT}")
    print("⚠️  DHYAN DEIN: Is black window (terminal) ko band MAT kijiye ga.")
    print("    Jab tak ye window open rahegi, tab tak website chalegi.")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=PORT, debug=False)
