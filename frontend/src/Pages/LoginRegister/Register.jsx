
import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import api from "../../Lib/api";
import { toast } from "react-toastify";
import useUserStore from "../../Stores/useUserStore";

const API_URL = "http://127.0.0.1:8000";

const Register = () => {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    full_name: "",
    username: "",
    email: "",
    password: "",
    confirm_password: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");


  const {isLoggedIn} = useUserStore()

  // Update form data whenever an input changes
  const handleChange = (e) => {
    const { name, value } = e.target;

    setFormData((prevData) => ({
      ...prevData,
      [name]: value,
    }));

    setError("");
    setSuccess("");
  };

  // Validate form data before calling backend
  const validateForm = () => {
    const { full_name, username, email, password, confirm_password } =
      formData;

    if (
      !full_name.trim() ||
      !username.trim() ||
      !email.trim() ||
      !password ||
      !confirm_password
    ) {
      return "Please fill in all fields.";
    }

    if (!/^[a-zA-Z0-9_]{3,20}$/.test(username)) {
      return "Username must be 3–20 characters and contain only letters, numbers, and underscores.";
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return "Please enter a valid email address.";
    }

    if (password.length < 8) {
      return "Password must contain at least 8 characters.";
    }

    if (password !== confirm_password) {
      return "Passwords do not match.";
    }

    return null;
  };

  // Call FastAPI backend
  const handleRegister = async (e) => {
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

      // Do not send confirm_password to the backend
      const payload = {
        full_name: formData.full_name.trim(),
        username: formData.username.trim(),
        email: formData.email.trim().toLowerCase(),
        password: formData.password,
        confirm_password:formData.confirm_password
      };

      const response = await api.post(
        `/auth/register`,
        payload
      );

      setSuccess(
        response.data.message || "Registration successful!"
      );

      setFormData({
        full_name: "",
        username: "",
        email: "",
        password: "",
        confirm_password: "",
      });

      toast.success("Successfully Register Now Please Login")
      navigate('/login')
      
    } catch (err) {
      const detail = err.response?.data?.detail;
      console.log(err);
      toast.error("Failed To Register")
      setError(
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
            ? detail.map((item) => item.msg).join(", ")
            : err.response?.data?.message ||
              "Registration failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

    useEffect(()=>{
      if(isLoggedIn){
        navigate('/')
      }
    },[isLoggedIn])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-10">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-lg">
        <div className="mb-7 text-center">
          <h1 className="text-3xl font-bold text-gray-900">
            Create an account
          </h1>

          <p className="mt-2 text-sm text-gray-500">
            Join EduNotes and access academic notes.
          </p>
        </div>

        {error && (
          <div
            role="alert"
            className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700"
          >
            {error}
          </div>
        )}

        {success && (
          <div
            role="status"
            className="mb-4 rounded-lg bg-green-50 p-3 text-sm text-green-700"
          >
            {success}
          </div>
        )}

        <form onSubmit={handleRegister} className="space-y-4">
          <div>
            <label
              htmlFor="full_name"
              className="mb-1 block text-sm font-medium text-gray-700"
            >
              Full name
            </label>

            <input
              id="full_name"
              name="full_name"
              type="text"
              autoComplete="name"
              placeholder="Enter your full name"
              value={formData.full_name}
              onChange={handleChange}
              disabled={loading}
              required
              className="w-full rounded-lg border border-gray-300 px-4 py-3 outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100"
            />
          </div>

          <div>
            <label
              htmlFor="username"
              className="mb-1 block text-sm font-medium text-gray-700"
            >
              Username
            </label>

            <input
              id="username"
              name="username"
              type="text"
              autoComplete="username"
              placeholder="Choose a username"
              value={formData.username}
              onChange={handleChange}
              disabled={loading}
              required
              className="w-full rounded-lg border border-gray-300 px-4 py-3 outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100"
            />
          </div>

          <div>
            <label
              htmlFor="email"
              className="mb-1 block text-sm font-medium text-gray-700"
            >
              Gmail / Email
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
              className="w-full rounded-lg border border-gray-300 px-4 py-3 outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="mb-1 block text-sm font-medium text-gray-700"
            >
              Password
            </label>

            <input
              id="password"
              name="password"
              type="password"
              autoComplete="new-password"
              placeholder="At least 8 characters"
              value={formData.password}
              onChange={handleChange}
              disabled={loading}
              required
              className="w-full rounded-lg border border-gray-300 px-4 py-3 outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100"
            />
          </div>

          <div>
            <label
              htmlFor="confirm_password"
              className="mb-1 block text-sm font-medium text-gray-700"
            >
              Confirm password
            </label>

            <input
              id="confirm_password"
              name="confirm_password"
              type="password"
              autoComplete="new-password"
              placeholder="Enter your password again"
              value={formData.confirm_password}
              onChange={handleChange}
              disabled={loading}
              required
              className="w-full rounded-lg border border-gray-300 px-4 py-3 outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-cyan-600 px-4 py-3 font-semibold text-white transition hover:bg-cyan-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Creating account..." : "Create account"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-gray-600">
          Already have an account?{" "}
          <Link
            to="/login"
            className="font-semibold text-cyan-700 hover:underline"
          >
            Login
          </Link>
        </p>
      </div>
    </div>
  );
};

export default Register;
