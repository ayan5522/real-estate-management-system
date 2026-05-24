"""
main.py - Real Estate Management System
Entry point: initialises DB, shows login, routes to correct dashboard.

FIX 1: Login widgets bleeding into dashboard
  - Root window is now kept hidden (root.withdraw())
  - Login runs in its own Toplevel window
  - On success: login Toplevel is destroyed, dashboard Toplevel opens
  - Root acts only as a hidden controller — never shows content itself

FIX 2: Login window not resizable
  - Handled inside login.py (resizable True, proper geometry, state zoomed on dashboard)
"""

import tkinter as tk
from tkinter import messagebox
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db


def main():
    # ── Initialise database ───────────────────────────────────────────────────
    try:
        db.initialize_database()
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Database Error",
            f"Could not connect to MySQL.\n\n{e}\n\n"
            "Please check db.py credentials and ensure MySQL is running."
        )
        root.destroy()
        sys.exit(1)

    # ── Hidden master root — never shown, just keeps the event loop alive ─────
    root = tk.Tk()
    root.withdraw()                         # invisible controller window
    root.title("Real Estate Management System")

    # ── Window tracker ────────────────────────────────────────────────────────
    windows = {"login": None, "dashboard": None}

    # ── Login success callback ────────────────────────────────────────────────
    def on_login_success(user, login_toplevel):
        # 1. Destroy the login window completely — no widgets survive
        login_toplevel.destroy()
        windows["login"] = None

        # 2. Open the dashboard in a fresh Toplevel
        dash_win = tk.Toplevel(root)
        windows["dashboard"] = dash_win

        # If user closes the dashboard window, quit the whole app
        dash_win.protocol("WM_DELETE_WINDOW", lambda: _quit())

        role = user.get("role", "agent")
        if role == "admin":
            from ui.admin_dashboard import AdminDashboard
            AdminDashboard(dash_win, user, lambda: on_logout(dash_win))
        else:
            from ui.agent_dashboard import AgentDashboard
            AgentDashboard(dash_win, user, lambda: on_logout(dash_win))

    # ── Logout callback ───────────────────────────────────────────────────────
    def on_logout(dash_win):
        dash_win.destroy()
        windows["dashboard"] = None
        show_login()

    # ── Quit helper ───────────────────────────────────────────────────────────
    def _quit():
        root.quit()
        root.destroy()

    # ── Show login ────────────────────────────────────────────────────────────
    def show_login():
        from ui.login import LoginWindow
        login_win = tk.Toplevel(root)
        windows["login"] = login_win
        # If user closes the login window, quit the app
        login_win.protocol("WM_DELETE_WINDOW", lambda: _quit())
        LoginWindow(login_win, on_login_success)

    show_login()
    root.mainloop()


if __name__ == "__main__":
    main()
