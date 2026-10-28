
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  FiUploadCloud,
  FiFileText,
  FiX,
  FiCheckCircle,
  FiAlertCircle,
  FiLoader,
} from "react-icons/fi";

import useFacultyStore from "../../Stores/facultiesStore";
import AuthorizedLayout from "../Authorized/Layouts/AuthorizedLayout";
import api from "../../Lib/api";
import axios from "axios";

const MAX_FILE_SIZE = 20 * 1024 * 1024;
const ALLOWED_EXTENSIONS = [".pdf", ".docx", ".ppt", ".pptx"];

const initialFormData = {
  title: "",
  description: "",
  faculty: "",
  programme: "",
  semester: "",
  subject: "",
};

const getErrorMessage = (err, fallback) => {
  const detail = err.response?.data?.detail;

  if (typeof detail === "string") return detail;

  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || "Invalid input").join(", ");
  }

  return err.response?.data?.message || fallback;
};

const getStudyOptions = (programme) => {
  if (!programme) return [];

  const totalYear = Number(programme.total_year);

  if (!Number.isInteger(totalYear) || totalYear < 1) {
    return [];
  }

  const total = programme.isSemesterWise
    ? totalYear * 2
    : totalYear;

  return Array.from({ length: total }, (_, index) => ({
    value: String(index + 1),
    label: programme.isSemesterWise
      ? `Semester ${index + 1}`
      : `Year ${index + 1}`,
  }));
};

export default function AddNote() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  // Read the existing faculty data from Zustand.
  const faculties = useFacultyStore((state) => state.data);
  const isFetched = useFacultyStore((state) => state.isFetched);
  const setData = useFacultyStore((state) => state.setData);
  const setIsFetched = useFacultyStore((state) => state.setIsFetched);
  const facultyLoading = useFacultyStore((state) => state.loading);
  const setFacultyLoading = useFacultyStore((state) => state.setLoading);
  const facultyError = useFacultyStore((state) => state.error);
  const setFacultyError = useFacultyStore((state) => state.setError);

  const [formData, setFormData] = useState(initialFormData);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Fetch faculties only when they are not already in the store.
  useEffect(() => {
    if (isFetched) return;

    let active = true;

    const fetchFaculties = async () => {
      setFacultyLoading(true);
      setFacultyError(null);

      try {
        const response = await api.get("/faculties");
        const result = response.data;

        const facultyList = Array.isArray(result)
          ? result
          : result?.data || result?.faculties || [];

        if (active) {
          setData(facultyList);
          setIsFetched(true);
        }
      } catch (err) {
        if (active) {
          setFacultyError(
            getErrorMessage(err, "Failed to load faculties.")
          );
        }
      } finally {
        if (active) setFacultyLoading(false);
      }
    };

    fetchFaculties();

    return () => {
      active = false;
    };
  }, [
    isFetched,
    setData,
    setIsFetched,
    setFacultyLoading,
    setFacultyError,
  ]);

  // Find the selected faculty using its ID.
  const selectedFaculty = faculties.find(
    (faculty) => String(faculty.id) === String(formData.faculty)
  );

  // Your faculty objects contain nested programs.
  const programmes = Array.isArray(selectedFaculty?.programs)
    ? selectedFaculty.programs
    : [];

  // Find the programme within the selected faculty.
  const selectedProgramme = programmes.find(
    (programme) =>
      String(programme.id) === String(formData.programme)
  );

  // Calculate semester/year choices from the programme properties.
  const studyOptions = getStudyOptions(selectedProgramme);

  const studyLabel = selectedProgramme?.isSemesterWise
    ? "Semester"
    : "Year";

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((previous) => {
      if (name === "faculty") {
        return {
          ...previous,
          faculty: value,
          programme: "",
          semester: "",
        };
      }

      if (name === "programme") {
        return {
          ...previous,
          programme: value,
          semester: "",
        };
      }

      return {
        ...previous,
        [name]: value,
      };
    });

    setError("");
    setSuccess("");
  };

  const handleFileChange = (event) => {
    const selectedFile = event.target.files?.[0];

    setFile(null);
    setError("");
    setSuccess("");

    if (!selectedFile) return;

    const dotIndex = selectedFile.name.lastIndexOf(".");
    const extension =
      dotIndex >= 0
        ? selectedFile.name.slice(dotIndex).toLowerCase()
        : "";

    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      setError("Only PDF, DOCX, PPT, and PPTX files are allowed.");
      event.target.value = "";
      return;
    }

    if (selectedFile.size === 0) {
      setError("The selected file is empty.");
      event.target.value = "";
      return;
    }

    if (selectedFile.size > MAX_FILE_SIZE) {
      setError("File size must be 20 MB or less.");
      event.target.value = "";
      return;
    }

    setFile(selectedFile);
  };

  const handleRemoveFile = () => {
    setFile(null);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const validateForm = () => {
    if (
      !formData.title.trim() ||
      !formData.faculty ||
      !formData.programme ||
      !formData.semester ||
      !formData.subject.trim()
    ) {
      return "Please complete all required fields.";
    }

    if (!selectedFaculty) {
      return "Please select a valid faculty.";
    }

    if (!selectedProgramme) {
      return "Please select a valid programme.";
    }

    if (
      !studyOptions.some(
        (option) => option.value === formData.semester
      )
    ) {
      return `Please select a valid ${studyLabel.toLowerCase()}.`;
    }

    if (!file) {
      return "Please select a file to upload.";
    }

    return null;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

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

    // Send the selected faculty and programme IDs.
    payload.append("faculty", selectedFaculty.id);
    payload.append("programme", selectedProgramme.id);

    // Semester-wise programmes send "semester".
    // Year-wise programmes send "year".
    payload.append(
      selectedProgramme.isSemesterWise ? "semester" : "year",
      formData.semester
    );

    payload.append("subject", formData.subject.trim());
    payload.append("file", file);

    try {
      setLoading(true);

      const token =
        localStorage.getItem("Token") ||
        localStorage.getItem("token");

      const response = await axios.post(
        "http://127.0.0.1:8000/api/v1/upload/notes",
        payload,
        {
          headers: {
            "Content-Type": "multipart/form-data",
            Authorization: `Bearer ${token}`,
           
          },
          withCredentials: true,
        }
      );

      setSuccess(
        response.data?.message || "Note uploaded successfully!"
      );

      setFormData(initialFormData);
      setFile(null);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }


    } catch (err) {
      console.log(err);
      setError(
        getErrorMessage(err, "Upload failed. Please try again.")
      );
    } finally {
      setLoading(false);
    }
  };

  const inputClass =
    "w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-cyan-500 focus:ring-4 focus:ring-cyan-500/10 disabled:cursor-not-allowed disabled:bg-slate-50";

  const labelClass =
    "mb-2 block text-sm font-semibold text-slate-700";

  return (
    <AuthorizedLayout>
      <main className="min-h-screen bg-slate-50 px-4 py-10 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-4xl">
          <div className="mb-8">
            <p className="mb-3 text-sm font-bold tracking-widest text-cyan-700">
              EDUNOTES / UPLOAD
            </p>

            <h1 className="text-3xl font-black tracking-tight text-slate-900 sm:text-4xl">
              Add academic notes
            </h1>

            <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-500 sm:text-base">
              Share academic materials organized by faculty,
              programme, semester or year, and subject.
            </p>
          </div>

          <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-8">
            {error && (
              <div
                role="alert"
                className="mb-6 flex items-start gap-3 rounded-xl border border-red-100 bg-red-50 p-4 text-sm text-red-700"
              >
                <FiAlertCircle className="mt-0.5 shrink-0 text-lg" />
                <span>{error}</span>
              </div>
            )}

            {success && (
              <div
                role="status"
                className="mb-6 flex items-start gap-3 rounded-xl border border-emerald-100 bg-emerald-50 p-4 text-sm text-emerald-700"
              >
                <FiCheckCircle className="mt-0.5 shrink-0 text-lg" />
                <span>{success}</span>
              </div>
            )}

            {facultyError && (
              <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
                <span>{facultyError}</span>

                <button
                  type="button"
                  onClick={() => {
                    setFacultyError(null);
                    setIsFetched(false);
                  }}
                  className="ml-2 font-bold underline"
                >
                  Retry
                </button>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="title" className={labelClass}>
                  Note title <span className="text-red-500">*</span>
                </label>

                <input
                  id="title"
                  name="title"
                  value={formData.title}
                  onChange={handleChange}
                  placeholder="e.g. Introduction to Python"
                  maxLength={150}
                  required
                  disabled={loading}
                  className={inputClass}
                />
              </div>

              <div>
                <label htmlFor="description" className={labelClass}>
                  Description
                </label>

                <textarea
                  id="description"
                  name="description"
                  rows={3}
                  value={formData.description}
                  onChange={handleChange}
                  placeholder="Briefly describe these notes..."
                  maxLength={2000}
                  disabled={loading}
                  className={`${inputClass} resize-y`}
                />
              </div>

              <div className="grid gap-6 sm:grid-cols-2">
                <div>
                  <label htmlFor="faculty" className={labelClass}>
                    Faculty <span className="text-red-500">*</span>
                  </label>

                  <select
                    id="faculty"
                    name="faculty"
                    value={formData.faculty}
                    onChange={handleChange}
                    required
                    disabled={loading || facultyLoading}
                    className={inputClass}
                  >
                    <option value="">
                      {facultyLoading
                        ? "Loading faculties..."
                        : "Select faculty"}
                    </option>

                    {faculties.map((faculty) => (
                      <option key={faculty.id} value={faculty.id}>
                        {faculty.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label htmlFor="programme" className={labelClass}>
                    Programme <span className="text-red-500">*</span>
                  </label>

                  <select
                    id="programme"
                    name="programme"
                    value={formData.programme}
                    onChange={handleChange}
                    required
                    disabled={
                      loading ||
                      !formData.faculty ||
                      programmes.length === 0
                    }
                    className={inputClass}
                  >
                    <option value="">
                      {!formData.faculty
                        ? "Select faculty first"
                        : programmes.length === 0
                          ? "No programmes available"
                          : "Select programme"}
                    </option>

                    {programmes.map((programme) => (
                      <option
                        key={programme.id}
                        value={programme.id}
                      >
                        {programme.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label htmlFor="semester" className={labelClass}>
                    {studyLabel}
                    <span className="text-red-500"> *</span>
                  </label>

                  <select
                    id="semester"
                    name="semester"
                    value={formData.semester}
                    onChange={handleChange}
                    required
                    disabled={
                      loading ||
                      !selectedProgramme ||
                      studyOptions.length === 0
                    }
                    className={inputClass}
                  >
                    <option value="">
                      {selectedProgramme
                        ? `Select ${studyLabel.toLowerCase()}`
                        : "Select programme first"}
                    </option>

                    {studyOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>

                  {selectedProgramme && studyOptions.length > 0 && (
                    <p className="mt-2 text-xs text-slate-500">
                      {selectedProgramme.isSemesterWise
                        ? `${selectedProgramme.totalYear} years · ${studyOptions.length} semesters`
                        : `${studyOptions.length} academic years`}
                    </p>
                  )}
                </div>

                <div>
                  <label htmlFor="subject" className={labelClass}>
                    Subject <span className="text-red-500">*</span>
                  </label>

                  <input
                    id="subject"
                    name="subject"
                    value={formData.subject}
                    onChange={handleChange}
                    placeholder="e.g. Data Structures"
                    maxLength={150}
                    required
                    disabled={loading}
                    className={inputClass}
                  />
                </div>
              </div>

              <div>
                <label htmlFor="file" className={labelClass}>
                  Upload file <span className="text-red-500">*</span>
                </label>

                <label
                  htmlFor="file"
                  className="flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50 px-5 py-10 text-center transition hover:border-cyan-400 hover:bg-cyan-50/50"
                >
                  <span className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-cyan-100 text-cyan-700">
                    <FiUploadCloud size={28} />
                  </span>

                  <span className="text-sm font-bold text-slate-800">
                    Click to select a file
                  </span>

                  <span className="mt-2 text-xs text-slate-500">
                    PDF, DOCX, PPT, PPTX · Maximum 20 MB
                  </span>

                  <input
                    ref={fileInputRef}
                    id="file"
                    type="file"
                    accept=".pdf,.docx,.ppt,.pptx"
                    onChange={handleFileChange}
                    disabled={loading}
                    className="sr-only"
                  />
                </label>

                {file && (
                  <div className="mt-4 flex items-center gap-3 rounded-xl border border-cyan-100 bg-cyan-50 p-4">
                    <FiFileText className="shrink-0 text-xl text-cyan-700" />

                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-semibold text-slate-800">
                        {file.name}
                      </p>

                      <p className="mt-1 text-xs text-slate-500">
                        {(file.size / (1024 * 1024)).toFixed(2)} MB
                      </p>
                    </div>

                    <button
                      type="button"
                      onClick={handleRemoveFile}
                      disabled={loading}
                      aria-label="Remove selected file"
                      className="rounded-lg p-2 text-slate-500 hover:bg-red-100 hover:text-red-600"
                    >
                      <FiX size={20} />
                    </button>
                  </div>
                )}
              </div>

              <div className="flex flex-col-reverse gap-3 border-t border-slate-100 pt-6 sm:flex-row sm:justify-end">
                <button
                  type="button"
                  onClick={() => navigate(-1)}
                  disabled={loading}
                  className="rounded-xl border border-slate-200 px-5 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  disabled={loading }
                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-cyan-700 px-6 py-3 text-sm font-bold text-white transition hover:bg-cyan-800 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {loading ? (
                    <>
                      <FiLoader className="animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <FiUploadCloud size={18} />
                      Upload notes
                    </>
                  )}
                </button>
              </div>
            </form>
          </section>

          <p className="mt-6 text-center text-xs leading-5 text-slate-400">
            Upload only academic materials you have permission to share.
          </p>
        </div>
      </main>
    </AuthorizedLayout>
  );
}
