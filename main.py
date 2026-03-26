import os
import threading
import time

# Flask imports
from app_flask import app

# Kivy imports
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.utils import platform

# On Android, we need a WebView. On Desktop (for testing), we just show a message.
if platform == 'android':
    from android.runnable import run_on_ui_thread
    from jnius import autoclass
    
    WebView = autoclass('android.webkit.WebView')
    WebViewClient = autoclass('android.webkit.WebViewClient')
    Activity = autoclass('org.kivy.android.PythonActivity').mActivity
else:
    # Desktop fallback
    run_on_ui_thread = lambda x: x


def start_flask():
    """Starts the Flask server in a background thread."""
    print("🚀 Starting local Flask server...")
    # Run Flask on localhost:5000
    # Use use_reloader=False because we are inside a thread
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)


class ATSApp(App):
    def build(self):
        # 1. Start Flask in a background thread
        threading.Thread(target=start_flask, daemon=True).start()
        
        # 2. Return a loading screen
        if platform == 'android':
            Clock.schedule_once(self.create_webview, 1)
            return Label(text="Starting ATS Analyzer Server...")
        else:
            return Label(text="Server running at http://127.0.0.1:5000\n(Use a browser to view)")

    @run_on_ui_thread
    def create_webview(self, *args):
        # Create and show the Android WebView
        webview = WebView(Activity)
        webview.getSettings().setJavaScriptEnabled(True)
        webview.getSettings().setDomStorageEnabled(True)
        webview.getSettings().setAllowFileAccess(True)
        webview.setWebViewClient(WebViewClient())
        
        Activity.setContentView(webview)
        webview.loadUrl("http://127.0.0.1:5000")


if __name__ == '__main__':
    ATSApp().run()
