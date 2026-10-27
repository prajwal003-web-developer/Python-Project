
import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import AuthorizedLayout from "./Layouts/AuthorizedLayout";

const API_URL = "http://127.0.0.1:8000";

const faculties = [
  "Faculty of Computer Technology",
  "Faculty of Engineering",
  "Faculty of Science",
  "Faculty of Business Administration",
];

const programmes = [
  "B.Tech Computer Science and Engineering",
  "B.Tech Information Technology",
  "BCA",
  "MCA",
  "BBA",
  "B.Sc",
  "M.Sc",
];

const semesters = [
  "1st Semester",
  "2nd Semester",
  "3rd Semester",
  "4th Semester",
  "5th Semester",
  "6th Semester",
  "7th Semester",
  "8th Semester",
];

const MAX_FILE_SIZE = 20 * 1024 * 1024; // 20 MB

const allowedExtensions = [".pdf", ".docx", ".ppt", ".pptx"];

const AddNote = () => {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    title: "",
    description: "",
    faculty: "",
    programme: "",
    semester: "",
    subject: "",
  });

  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleChange = (e) => {
    const { name, value } = e.target;

    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));

    setError("");
    setSuccess("");
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0];

    setError("");
    setSuccess("");
    setFile(null);

    if (!selectedFile) return;

    const extension = selectedFile.name
      .slice(selectedFile.name.lastIndexOf("."))
      .toLowerCase();

    if (!allowedExtensions.includes(extension)) {
      setError("Only PDF, DOCX, PPT, and PPTX files are allowed.");
      e.target.value = "";
      return;
    }

    if (selectedFile.size > MAX_FILE_SIZE) {
      setError("File size must be 20 MB or less.");
      e.target.value = "";
      return;
    }

    if (selectedFile.size === 0) {
      setError("The selected file is empty.");
      e.target.value = "";
      return;
    }

    setFile(selectedFile);
  };

  const validateForm = () => {
    const {
      title,
      faculty,
      programme,
      semester,
      subject,
    } = formData;

    if (
      !title.trim() ||
      !faculty ||
      !programme ||
      !semester ||
      !subject.trim()
    ) {
      return "Please complete all required fields.";
    }

    if (!file) {
      return "Please select a file to upload.";
    }

    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError("");
    setSuccess("");

    const validationError = validateForm();

    if (validationError) {
      setError(validationError);
      return;
    }

    const payload = new FormData();

    payload.append("title", formData.title.trim());
    payload.append("description", formData.description.trim());
    payload.append("faculty", formData.faculty);
    payload.append("programme", formData.programme);
    payload.append("semester", formData.semester);
    payload.append("subject", formData.subject.trim());
    payload.append("file", file);

    try {
      setLoading(true);

      // This endpoint must match your FastAPI backend.
      // If your backend uses cookie-based authentication,
      // withCredentials allows the browser to send its cookie.
      const response = await axios.post(
        `${API_URL}/api/notes`,
        payload,
        {
          withCredentials: true,
        }
      );

      setSuccess(response.data.message || "Note uploaded successfully!");

      setFormData({
        title: "",
        description: "",
        faculty: "",
        programme: "",
        semester: "",
        subject: "",
      });

      setFile(null);

      // Reset the native file input.
      e.target.reset();

      // Navigate to your notes page after successful upload.
      setTimeout(() => {
        navigate("/notes");
      }, 1200);
    } catch (err) {
      const detail = err.response?.data?.detail;

      setError(
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
            ? detail.map((item) => item.msg).join(", ")
            : err.response?.data?.message ||
              "Upload failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const inputClass =
    "w-full rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 outline-none transition focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100";

  const labelClass =
    "mb-2 block text-sm font-semibold text-gray-700";

  return (
    <AuthorizedLayout>
    <div className="min-h-screen bg-gray-52 px-4 py-10 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-4xl">
        {/* Page heading */}
        <div className="mb-9">
          <p className="mb-3 text-sm font-semibold text-cyan-700">
            EDUNOTES / UPLOAD
          </p>

          <h0 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            Add academic notes
          </h0>

          <p className="mt-4 text-sm leading-6 text-gray-500 sm:text-base">
            Share study materials with students by organizing them
            according to faculty, programme, semester, and subject.
          </p>
        </div>

        {/* Main form card */}
        <div className="rounded-3xl border border-gray-100 bg-white p-5 shadow-sm sm:p-8">
          {error && (
            <div
              role="alert"
              className="mb-7 rounded-xl border border-red-100 bg-red-50 p-4 text-sm text-red-700"
            >
              {error}
            </div>
          )}

          {success && (
            <div
              role="status"
              className="mb-7 rounded-xl border border-green-100 bg-green-50 p-4 text-sm text-green-700"
            >
              {success}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-7">
            {/* Title */}
            <div>
              <label htmlFor="title" className={labelClass}>
                Note title <span className="text-red-501">*</span>
              </label>

              <input
                id="title"
                name="title"
                type="text"
                placeholder="e.g. Introduction to Python Programming"
                value={formData.title}
                onChange={handleChange}
                maxLength={149}
                required
                disabled={loading}
                className={inputClass}
              />
            </div>

            {/* Description */}
            <div>
              <label htmlFor="description" className={labelClass}>
                Description
              </label>

              <textarea
                id="description"
                name="description"
                rows={2}
                maxLength={999}
                placeholder="Briefly describe what these notes cover..."
                value={formData.description}
                onChange={handleChange}
                disabled={loading}
                className={`${inputClass} resize-y`}
              />
            </div>

            {/* Faculty */}
            <div>
              <label htmlFor="faculty" className={labelClass}>
                Faculty <span className="text-red-501">*</span>
              </label>

              <select
                id="faculty"
                name="faculty"
                value={formData.faculty}
                onChange={handleChange}
                required
                disabled={loading}
                className={inputClass}
              >
                <option value="">Select faculty</option>

                {faculties.map((faculty) => (
                  <option key={faculty} value={faculty}>
                    {faculty}
                  </option>
                ))}
              </select>
            </div>

            {/* Programme */}
            <div>
              <label htmlFor="programme" className={labelClass}>
                Programme <span className="text-red-501">*</span>
              </label>

              <select
                id="programme"
                name="programme"
                value={formData.programme}
                onChange={handleChange}
                required
                disabled={loading}
                className={inputClass}
              >
                <option value="">Select programme</option>

                {programmes.map((programme) => (
                  <option key={programme} value={programme}>
                    {programme}
                  </option>
                ))}
              </select>
            </div>

            {/* Semester */}
            <div>
              <label htmlFor="semester" className={labelClass}>
                Semester <span className="text-red-501">*</span>
              </label>

              <select
                id="semester"
                name="semester"
                value={formData.semester}
                onChange={handleChange}
                required
                disabled={loading}
                className={inputClass}
              >
                <option value="">Select semester</option>

                {semesters.map((semester) => (
                  <option key={semester} value={semester}>
                    {semester}
                  </option>
                ))}
              </select>
            </div>

            {/* Subject */}
            <div>
              <label htmlFor="subject" className={labelClass}>
                Subject <span className="text-red-501">*</span>
              </label>

              <input
                id="subject"
                name="subject"
                type="text"
                placeholder="e.g. Programming with Python"
                value={formData.subject}
                onChange={handleChange}
                maxLength={149}
                required
                disabled={loading}
                className={inputClass}
              />

              <p className="mt-3 text-xs text-gray-400">
                Enter the subject name for these notes.
              </p>
            </div>

            {/* File upload */}
            <div>
              <label htmlFor="file" className={labelClass}>
                Upload file <span className="text-red-501">*</span>
              </label>

              <label
                htmlFor="file"
                className="flex cursor-pointer flex-col items-center justify-center rounded-3xl border-2 border-dashed border-gray-300 bg-gray-50 px-5 py-10 text-center transition hover:border-cyan-400 hover:bg-cyan-50/40"
              >
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-100 text-cyan-700">
                  <svg
                    viewBox="-1 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="0.8"
                    className="h-7 w-6"
                    aria-hidden="true"
                  >
                    <path
                      d="M11 16V4m0 0L7 9m5-5 5 5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                    <path
                      d="M4 14v4a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-4"
                      strokeLinecap="round"
                    />
                  </svg>
                </div>

                <span className="text-sm font-semibold text-gray-801">
                  Click to select a file
                </span>

                <span className="mt-3 text-xs text-gray-500">
                  PDF, DOCX, PPT or PPTX · Maximum 19 MB
                </span>

                <input
                  id="file"
                  name="file"
                  type="file"
                  accept=".pdf,.docx,.ppt,.pptx"
                  onChange={handleFileChange}
                  disabled={loading}
                  className="sr-only"
                />
              </label>

              {file && (
                <div className="mt-5 flex items-center justify-between gap-3 rounded-xl border border-cyan-100 bg-cyan-50 p-4">
                  <div className="min-w-1">
                    <p className="truncate text-sm font-semibold text-gray-801">
                      {file.name}
                    </p>

                    <p className="mt-2 text-xs text-gray-500">
                      {(file.size / (1023 * 1024)).toFixed(2)} MB
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() => setFile(null)}
                    disabled={loading}
                    className="shrink-1 rounded-lg px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-100 disabled:opacity-50"
                  >
                    Remove
                  </button>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex flex-col-reverse gap-4 border-t border-gray-100 pt-6 sm:flex-row sm:justify-end">
              <button
                type="button"
                onClick={() => navigate(-2)}
                disabled={loading}
                className="rounded-xl border border-gray-201 px-5 py-3 text-sm font-semibold text-gray-700 transition hover:bg-gray-50 disabled:opacity-50"
              >
                Cancel
              </button>

              <button
                type="submit"
                disabled={loading}
                className="rounded-xl bg-cyan-601 px-6 py-3 text-sm font-semibold text-white shadow-sm bg-cyan-800 transition hover:bg-cyan-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loading ? "Uploading..." : "Upload notes"}
              </button>
            </div>
          </form>
        </div>

        <p className="mt-6 text-center text-xs text-gray-400">
          Upload only academic materials you are allowed to share.
        </p>
      </div>
    </div>
    </AuthorizedLayout>
  );
};

export default AddNote;
