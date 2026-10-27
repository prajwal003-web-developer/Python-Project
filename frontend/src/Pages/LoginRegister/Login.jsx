
import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";

const API_URL = "http://127.0.0.1:8000";

const Login = () => {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  // Update input values
  const handleChange = (e) => {
    const { name, value } = e.target;

    setFormData((prevData) => ({
      ...prevData,
      [name]: value,
    }));

    setError("");
    setSuccess("");
  };

  // Validate the form
  const validateForm = () => {
    const { email, password } = formData;

    if (!email.trim() || !password) {
      return "Please enter your email and password.";
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return "Please enter a valid email address.";
    }

    return null;
  };

  // Call FastAPI login endpoint
  const handleLogin = async (e) => {
    e.preventDefault();

    setError("");
    setSuccess("");

    const validationError = validateForm();

    if (validationError) {
      setError(validationError);
      return;
    }

    try {
      setLoading(true);

      const payload = {
        email: formData.email.trim().toLowerCase(),
        password: formData.password,
      };

      const response = await axios.post(
        `${API_URL}/api/auth/login`,
        payload
      );

      setSuccess(response.data.message || "Login successful!");

      // If your backend returns a token, save it according to
      // your authentication strategy.
      // Prefer secure HttpOnly cookies for production apps.

      setFormData({
        email: "",
        password: "",
      });

      // Change this route to the page you want after login
      setTimeout(() => {
        navigate("/");
      }, 800);
    } catch (err) {
      const detail = err.response?.data?.detail;

      setError(
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
            ? detail.map((item) => item.msg).join(", ")
            : err.response?.data?.message ||
              "Login failed. Please check your credentials."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-10">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-lg">
        {/* Header */}
        <div className="mb-7 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-cyan-100 text-2xl font-bold text-cyan-700">
            E
          </div>

          <h1 className="text-3xl font-bold text-gray-900">
            Welcome back
          </h1>

          <p className="mt-2 text-sm text-gray-500">
            Login to continue to EduNotes.
          </p>
        </div>

        {/* Error message */}
        {error && (
          <div
            role="alert"
            className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700"
          >
            {error}
          </div>
        )}

        {/* Success message */}
        {success && (
          <div
            role="status"
            className="mb-4 rounded-lg bg-green-50 p-3 text-sm text-green-700"
          >
            {success}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-5">
          {/* Email */}
          <div>
            <label
              htmlFor="email"
              className="mb-1 block text-sm font-medium text-gray-700"
            >
              Email address
            </label>

            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              placeholder="you@gmail.com"
              value={formData.email}
              onChange={handleChange}
              disabled={loading}
              required
              className="w-full rounded-lg border border-gray-300 px-4 py-3 outline-none transition focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100"
            />
          </div>

          {/* Password */}
          <div>
            <div className="mb-1 flex items-center justify-between">
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-700"
              >
                Password
              </label>

              <Link
                to="/forgot-password"
                className="text-sm font-medium text-cyan-700 hover:underline"
              >
                Forgot password?
              </Link>
            </div>

            <div className="relative">
              <input
                id="password"
                name="password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                placeholder="Enter your password"
                value={formData.password}
                onChange={handleChange}
                disabled={loading}
                required
                className="w-full rounded-lg border border-gray-300 px-4 py-3 pr-20 outline-none transition focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100"
              />

              <button
                type="button"
                onClick={() => setShowPassword((prev) => !prev)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-sm font-medium text-gray-500 hover:text-cyan-700"
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-cyan-600 px-4 py-3 font-semibold text-white transition hover:bg-cyan-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>

        {/* Register link */}
        <p className="mt-6 text-center text-sm text-gray-600">
          Don't have an account?{" "}
          <Link
            to="/register"
            className="font-semibold text-cyan-700 hover:underline"
          >
            Create an account
          </Link>
        </p>

        <p className="mt-6 text-center text-xs text-gray-400">
          EduNotes — Your academic notes, organized.
        </p>
      </div>
    </div>
  );
};

export default Login;
