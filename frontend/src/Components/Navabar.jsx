
import React, { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import {
  FiSearch,
  FiMenu,
  FiX,
  FiUser,
  FiLogOut,
  FiBookOpen,
  FiBookmark,
  FiLayout,
  FiLogIn,
  FiUserPlus,
  
} from "react-icons/fi";
import Logo from "./Logo";
import { FaGraduationCap } from "react-icons/fa";

const Navbar = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  // Temporary authentication state.
  // Replace this with your actual authentication logic later.
  const isLoggedIn = false;

  const user = {
    name: "Student",
    email: "student@example.com",
  };

  const navigate = useNavigate();

  const closeMobileMenu = () => {
    setMobileMenuOpen(false);
    setUserMenuOpen(false);
  };

  const navLinkClass = ({ isActive }) =>
    `flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition-all duration-200 ${
      isActive
        ? "bg-cyan-50 text-cyan-700"
        : "text-gray-600 hover:bg-gray-100 hover:text-cyan-700"
    }`;

  const handleSearch = (e) => {
    e.preventDefault();

    const query = searchQuery.trim();

    if (!query) return;

    closeMobileMenu();
    navigate(`/search?q=${encodeURIComponent(query)}`);
  };

  const handleLogout = () => {
    setUserMenuOpen(false);
    closeMobileMenu();

    // Add your logout logic here when authentication is implemented.
    navigate("/");
  };

  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-gray-100 bg-white/95 shadow-sm backdrop-blur-md">
      <nav className="mx-auto flex h-[76px] max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        {/* Logo */}
        <Link
          to="/"
          onClick={closeMobileMenu}
          className="shrink-0"
          aria-label="ADTU Notes home"
        >
          <Logo />
        </Link>

        {/* Desktop Navigation */}
        <div className="hidden items-center gap-1 lg:flex">
          <NavLink to="/" end className={navLinkClass}>
            <FiLayout size={17} />
            Home
          </NavLink>

          <NavLink to="/saved" className={navLinkClass}>
            <FiBookOpen size={17} />
            Saved Notes
          </NavLink>

          {/* Direct navigation: no dropdown */}
          <NavLink to="/faculty" className={navLinkClass}>
            <FaGraduationCap size={18} />
            Faculties
          </NavLink>
        </div>

        {/* Desktop Search */}
        <form
          onSubmit={handleSearch}
          className="hidden max-w-xs flex-1 items-center rounded-xl border border-gray-200 bg-gray-50 px-3 transition focus-within:border-cyan-400 focus-within:bg-white focus-within:ring-2 focus-within:ring-cyan-100 md:flex lg:max-w-sm"
        >
          <FiSearch className="shrink-0 text-gray-400" size={19} />

          <input
            type="search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search notes, subjects..."
            aria-label="Search notes"
            className="w-full bg-transparent px-3 py-2.5 text-sm text-gray-700 outline-none placeholder:text-gray-400"
          />

          <button
            type="submit"
            aria-label="Submit search"
            className="rounded-lg p-1.5 text-gray-500 transition hover:bg-cyan-50 hover:text-cyan-700"
          >
            <FiSearch size={17} />
          </button>
        </form>

        {/* Desktop Authentication */}
        <div className="hidden items-center gap-2 lg:flex">
          {isLoggedIn ? (
            <div className="relative">
              <button
                type="button"
                onClick={() => setUserMenuOpen((prev) => !prev)}
                aria-expanded={userMenuOpen}
                aria-label="Open user menu"
                className="flex items-center gap-3 rounded-xl border border-gray-200 px-3 py-2 transition hover:bg-gray-50"
              >
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-cyan-100 text-cyan-700">
                  <FiUser size={19} />
                </div>

                <div className="text-left">
                  <p className="max-w-32 truncate text-sm font-semibold text-gray-800">
                    {user.name}
                  </p>
                  <p className="max-w-32 truncate text-xs text-gray-500">
                    {user.email}
                  </p>
                </div>
              </button>

              {userMenuOpen && (
                <div className="absolute right-0 top-full mt-2 w-56 rounded-2xl border border-gray-100 bg-white p-2 shadow-xl">
                  <Link
                    to="/profile"
                    onClick={() => setUserMenuOpen(false)}
                    className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-gray-600 hover:bg-gray-50 hover:text-cyan-700"
                  >
                    <FiUser size={17} />
                    My Profile
                  </Link>

                  <Link
                    to="/my-notes"
                    onClick={() => setUserMenuOpen(false)}
                    className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-gray-600 hover:bg-gray-50 hover:text-cyan-700"
                  >
                    <FiBookmark size={17} />
                    My Notes
                  </Link>

                  <button
                    type="button"
                    onClick={handleLogout}
                    className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm text-red-600 hover:bg-red-50"
                  >
                    <FiLogOut size={17} />
                    Logout
                  </button>
                </div>
              )}
            </div>
          ) : (
            <>
              <NavLink
                to="/login"
                className={({ isActive }) =>
                  `flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition ${
                    isActive
                      ? "bg-gray-100 text-cyan-700"
                      : "text-gray-600 hover:bg-gray-100 hover:text-cyan-700"
                  }`
                }
              >
                <FiLogIn size={17} />
                Login
              </NavLink>

              <Link
                to="/register"
                className="flex items-center gap-2 rounded-xl bg-cyan-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-cyan-700 hover:shadow-md"
              >
                <FiUserPlus size={17} />
                Register
              </Link>
            </>
          )}
        </div>

        {/* Mobile Menu Button */}
        <button
          type="button"
          onClick={() => setMobileMenuOpen((prev) => !prev)}
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-gray-200 text-gray-700 transition hover:bg-gray-100 lg:hidden"
          aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
          aria-expanded={mobileMenuOpen}
        >
          {mobileMenuOpen ? <FiX size={22} /> : <FiMenu size={22} />}
        </button>
      </nav>

      {/* Mobile Navigation */}
      {mobileMenuOpen && (
        <div className="border-t border-gray-100 bg-white px-4 pb-5 pt-4 shadow-lg lg:hidden">
          <div className="mx-auto max-w-7xl space-y-4">
            {/* Mobile Search */}
            <form
              onSubmit={handleSearch}
              className="flex items-center rounded-xl border border-gray-200 bg-gray-50 px-3 focus-within:border-cyan-400 focus-within:ring-2 focus-within:ring-cyan-100"
            >
              <FiSearch className="shrink-0 text-gray-400" size={19} />

              <input
                type="search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search notes, subjects..."
                aria-label="Search notes"
                className="w-full bg-transparent px-3 py-3 text-sm outline-none placeholder:text-gray-400"
              />

              <button
                type="submit"
                aria-label="Submit search"
                className="p-2 text-gray-500 hover:text-cyan-700"
              >
                <FiSearch size={18} />
              </button>
            </form>

            {/* Mobile Links */}
            <div className="space-y-1">
              <NavLink
                to="/"
                end
                onClick={closeMobileMenu}
                className={navLinkClass}
              >
                <FiLayout size={18} />
                Home
              </NavLink>

              <NavLink
                to="/saved"
                onClick={closeMobileMenu}
                className={navLinkClass}
              >
                <FiBookOpen size={18} />
                Saved Notes
              </NavLink>

              {/* Direct navigation: no dropdown */}
              <NavLink
                to="/faculty"
                onClick={closeMobileMenu}
                className={navLinkClass}
              >
                <FaGraduationCap size={18} />
                Faculties
              </NavLink>
            </div>

            <div className="border-t border-gray-100 pt-4">
              {isLoggedIn ? (
                <div className="space-y-2">
                  <div className="mb-3 flex items-center gap-3 rounded-xl bg-gray-50 p-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-cyan-100 text-cyan-700">
                      <FiUser size={20} />
                    </div>

                    <div className="min-w-0">
                      <p className="truncate text-sm font-semibold text-gray-800">
                        {user.name}
                      </p>
                      <p className="truncate text-xs text-gray-500">
                        {user.email}
                      </p>
                    </div>
                  </div>

                  <NavLink
                    to="/profile"
                    onClick={closeMobileMenu}
                    className={navLinkClass}
                  >
                    <FiUser size={18} />
                    My Profile
                  </NavLink>

                  <NavLink
                    to="/my-notes"
                    onClick={closeMobileMenu}
                    className={navLinkClass}
                  >
                    <FiBookmark size={18} />
                    My Notes
                  </NavLink>

                  <button
                    type="button"
                    onClick={handleLogout}
                    className="flex w-full items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium text-red-600 transition hover:bg-red-50"
                  >
                    <FiLogOut size={18} />
                    Logout
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-3">
                  <Link
                    to="/login"
                    onClick={closeMobileMenu}
                    className="flex items-center justify-center gap-2 rounded-xl border border-gray-200 px-3 py-3 text-sm font-semibold text-gray-700 transition hover:border-cyan-200 hover:bg-cyan-50 hover:text-cyan-700"
                  >
                    <FiLogIn size={17} />
                    Login
                  </Link>

                  <Link
                    to="/register"
                    onClick={closeMobileMenu}
                    className="flex items-center justify-center gap-2 rounded-xl bg-cyan-600 px-3 py-3 text-sm font-semibold text-white transition hover:bg-cyan-700"
                  >
                    <FiUserPlus size={17} />
                    Register
                  </Link>
                </div>
              )}
            </div>

            <p className="pt-1 text-center text-xs text-gray-400">
              ADTU Notes — Your learning resources, organized.
            </p>
          </div>
        </div>
      )}
    </header>
  );
};

export default Navbar;
