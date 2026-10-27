
import React, { useState } from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  BookOpen,
  House,
  FilePlus2,
  Files,
  Menu,
  X,
  LogOut,
  UserRound,
  ChevronDown,
} from "lucide-react";
import axios from "axios";

const API_URL = "http://127.0.0.1:8000";

// ---------------- NAVBAR ----------------

const AuthorizedNavbar = () => {
  const [menuOpen, setMenuOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);

  const navigate = useNavigate();

  const navItems = [
    {
      label: "Home",
      path: "/",
      icon: House,
    },
    {
      label: "Add Notes",
      path: "/add",
      icon: FilePlus2,
    },
    {
      label: "My Notes",
      path: "/my-notes",
      icon: Files,
    },
  ];

  const navLinkClass = ({ isActive }) =>
    `flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition ${
      isActive
        ? "bg-cyan-50 text-cyan-700"
        : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
    }`;

  const handleLogout = async () => {
    if (loggingOut) return;

    setLoggingOut(true);

    try {
      // Update this endpoint to match your FastAPI backend.
      await axios.post(
        `${API_URL}/api/auth/logout`,
        {},
        { withCredentials: true }
      );

      navigate("/login", { replace: true });
    } catch (error) {
      console.error("Logout failed:", error);
      alert("Could not log out. Please try again.");
    } finally {
      setLoggingOut(false);
      setProfileOpen(false);
      setMenuOpen(false);
    }
  };

  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-gray-200 bg-white/95 shadow-sm backdrop-blur-md">
      <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Logo */}
        <Link
          to="/"
          onClick={() => setMenuOpen(false)}
          className="flex shrink-0 items-center gap-2.5"
        >
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-600 text-white shadow-sm">
            <BookOpen size={22} />
          </div>

          <div>
            <span className="text-xl font-bold tracking-tight text-gray-900">
              Edu<span className="text-cyan-600">Notes</span>
            </span>
            <p className="-mt-0.5 hidden text-[10px] font-medium tracking-wide text-gray-400 sm:block">
              YOUR ACADEMIC LIBRARY
            </p>
          </div>
        </Link>

        {/* Desktop navigation */}
        <div className="hidden items-center gap-1 md:flex">
          {navItems.map((item) => {
            const Icon = item.icon;

            return (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === "/"}
                className={navLinkClass}
              >
                <Icon size={17} />
                {item.label}
              </NavLink>
            );
          })}
        </div>

        {/* Desktop profile */}
        <div className="relative hidden md:block">
          <button
            type="button"
            onClick={() => setProfileOpen((prev) => !prev)}
            aria-expanded={profileOpen}
            className="flex items-center gap-2 rounded-xl border border-gray-200 px-3 py-2 transition hover:bg-gray-50"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-cyan-100 text-cyan-700">
              <UserRound size={17} />
            </div>

            <span className="text-sm font-semibold text-gray-700">
              Account
            </span>

            <ChevronDown size={15} className="text-gray-400" />
          </button>

          {profileOpen && (
            <div className="absolute right-0 top-12 w-48 rounded-xl border border-gray-100 bg-white p-2 shadow-lg">
              <button
                type="button"
                onClick={handleLogout}
                disabled={loggingOut}
                className="flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-50"
              >
                <LogOut size={16} />
                {loggingOut ? "Logging out..." : "Logout"}
              </button>
            </div>
          )}
        </div>

        {/* Mobile menu button */}
        <button
          type="button"
          onClick={() => setMenuOpen((prev) => !prev)}
          aria-label={menuOpen ? "Close navigation" : "Open navigation"}
          aria-expanded={menuOpen}
          className="flex h-10 w-10 items-center justify-center rounded-xl border border-gray-200 text-gray-700 transition hover:bg-gray-100 md:hidden"
        >
          {menuOpen ? <X size={21} /> : <Menu size={21} />}
        </button>
      </nav>

      {/* Mobile navigation */}
      {menuOpen && (
        <div className="border-t border-gray-100 bg-white px-4 py-4 shadow-lg md:hidden">
          <div className="mx-auto max-w-7xl space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;

              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  end={item.path === "/"}
                  onClick={() => setMenuOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition ${
                      isActive
                        ? "bg-cyan-50 text-cyan-700"
                        : "text-gray-600 hover:bg-gray-50"
                    }`
                  }
                >
                  <Icon size={19} />
                  {item.label}
                </NavLink>
              );
            })}

            <div className="my-3 border-t border-gray-100" />

            <button
              type="button"
              onClick={handleLogout}
              disabled={loggingOut}
              className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-red-600 transition hover:bg-red-50 disabled:opacity-50"
            >
              <LogOut size={19} />
              {loggingOut ? "Logging out..." : "Logout"}
            </button>
          </div>
        </div>
      )}
    </header>
  );
};

// ---------------- AUTHORIZED LAYOUT ----------------

const AuthorizedLayout = ({children}) => {
  return (
    <div className="min-h-screen bg-gray-50">
      <AuthorizedNavbar />

      {/* Offset for the fixed navbar */}
      <main className="min-h-screen pt-16">
        {children}
      </main>
    </div>
  );
};

export default AuthorizedLayout;
