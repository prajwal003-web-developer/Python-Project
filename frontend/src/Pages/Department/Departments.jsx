
import React, { useEffect, useState } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import {
  FiArrowLeft,
  FiArrowRight,
  FiBookOpen,
  FiChevronDown,
  FiRefreshCw,
} from "react-icons/fi";

import HomeLayout from "../../Components/Layouts/HomeLayout";
import Loading from "../../Components/Loading";
import useFacultyStore from "../../Stores/facultiesStore";

const Departments = () => {
  const { facultyId } = useParams();
  const navigate = useNavigate();

  const [expandedDepartment, setExpandedDepartment] = useState(null);

  const {
    data: faculties,
    isFetched,
    setIsFetched,
    setData,
    loading,
    setLoading,
    error,
    setError,
  } = useFacultyStore();

  const dummyFaculties = [
    {
      id: "engineering",
      name: "Engineering",
      departments: [
        { id: "cse", name: "Computer Science & Engineering" },
        { id: "it", name: "Information Technology" },
        { id: "civil", name: "Civil Engineering" },
        { id: "mechanical", name: "Mechanical Engineering" },
        { id: "electrical", name: "Electrical Engineering" },
      ],
    },
    {
      id: "science",
      name: "Science",
      departments: [
        { id: "physics", name: "Physics" },
        { id: "chemistry", name: "Chemistry" },
        { id: "mathematics", name: "Mathematics" },
      ],
    },
    {
      id: "management",
      name: "Management",
      departments: [
        { id: "business", name: "Business Administration" },
        { id: "commerce", name: "Commerce" },
      ],
    },
    {
      id: "humanities",
      name: "Humanities",
      departments: [
        { id: "english", name: "English" },
        { id: "economics", name: "Economics" },
      ],
    },
  ];

  const fetchFaculties = async () => {
    setLoading(true);
    setError(null);

    try {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setData(dummyFaculties);
      setIsFetched(true);
    } catch {
      setError("Failed to load departments. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!isFetched || faculties.length === 0) {
      fetchFaculties();
    }
  }, []);

  const faculty = faculties.find((item) => item.id === facultyId);

  const handleDepartmentClick = (departmentId) => {
    setExpandedDepartment((current) =>
      current === departmentId ? null : departmentId
    );
  };

  const handleSemesterClick = (departmentId, semester) => {
    navigate(`/faculty/${facultyId}/${departmentId}/${semester}`);
  };

  return (
    <HomeLayout>
      <div className="min-h-screen bg-gray-50 px-4 sm:px-8">
        <div className="mx-auto max-w-6xl">
          <Link
            to="/faculty"
            className="mb-6 inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-gray-600 transition hover:bg-white hover:text-cyan-600"
          >
            <FiArrowLeft />
            Back to Faculties
          </Link>

          <div className="mb-8">
            <p className="mb-2 text-sm font-semibold uppercase tracking-wider text-cyan-600">
              Academic Departments
            </p>

            <h1 className="text-3xl font-bold text-gray-900 sm:text-4xl">
              {faculty?.name || "Departments"}
            </h1>

            <p className="mt-2 text-gray-500">
              Select a department to view its available semesters.
            </p>
          </div>

          {loading && <Loading message="Loading departments..." />}

          {!loading && error && (
            <div className="rounded-2xl border border-red-100 bg-white p-8 text-center shadow-sm">
              <p className="mb-4 text-red-600">{error}</p>

              <button
                onClick={fetchFaculties}
                className="inline-flex items-center gap-2 rounded-lg bg-cyan-600 px-4 py-2 text-white transition hover:bg-cyan-700"
              >
                <FiRefreshCw />
                Try Again
              </button>
            </div>
          )}

          {!loading && !error && isFetched && !faculty && (
            <div className="rounded-2xl bg-white p-10 text-center shadow-inner shadow-gray-200">
              <h2 className="text-xl font-semibold text-gray-800">
                Faculty not found
              </h2>

              <p className="mt-2 text-gray-500">
                Please select a valid faculty.
              </p>

              <Link
                to="/faculties"
                className="mt-5 inline-block rounded-lg bg-cyan-600 px-5 py-2.5 text-white hover:bg-cyan-700"
              >
                View Faculties
              </Link>
            </div>
          )}

          {!loading && !error && faculty && (
            <div className="space-y-4">
              {faculty.departments.map((department) => {
                const isExpanded =
                  expandedDepartment === department.id;

                return (
                  <div
                    key={department.id}
                    className="overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-inner shadow-gray-200 transition hover:border-cyan-100"
                  >
                    {/* Department header */}
                    <button
                      type="button"
                      onClick={() =>
                        handleDepartmentClick(department.id)
                      }
                      aria-expanded={isExpanded}
                      className="flex w-full items-center justify-between gap-4 p-5 text-left sm:p-6"
                    >
                      <div className="flex min-w-0 items-center gap-4">
                        <div className="shrink-0 rounded-xl bg-cyan-50 p-3 text-cyan-600">
                          <FiBookOpen size={23} />
                        </div>

                        <div>
                          <h2 className="font-bold text-gray-800 transition hover:text-cyan-700 sm:text-lg">
                            {department.name}
                          </h2>

                          <p className="mt-1 text-sm text-gray-500">
                            {isExpanded
                              ? "Choose a semester below"
                              : "Click to view semesters"}
                          </p>
                        </div>
                      </div>

                      <FiChevronDown
                        size={21}
                        className={`shrink-0 text-gray-500 transition-transform duration-300 ${
                          isExpanded ? "rotate-180 text-cyan-600" : ""
                        }`}
                      />
                    </button>

                    {/* Expandable semester section */}
                    {isExpanded && (
                      <div className="border-t border-gray-100 bg-gray-50 p-5 sm:p-6">
                        <div className="mb-4">
                          <h3 className="font-semibold text-gray-800">
                            Select Semester / Year
                          </h3>

                          <p className="mt-1 text-sm text-gray-500">
                            Choose one to explore its subjects and notes.
                          </p>
                        </div>

                        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                          {Array.from(
                            { length: 8 },
                            (_, index) => index + 1
                          ).map((semester) => (
                            <button
                              key={semester}
                              type="button"
                              onClick={() =>
                                handleSemesterClick(
                                  department.id,
                                  semester
                                )
                              }
                              className="group flex items-center justify-between gap-2 rounded-xl border border-gray-200 bg-white p-4 text-left transition hover:border-cyan-400 hover:bg-cyan-50 hover:shadow-sm"
                            >
                              <div>
                                <p className="text-sm font-bold text-gray-800 group-hover:text-cyan-700">
                                  Semester {semester}
                                </p>

                                <p className="mt-1 text-xs text-gray-500">
                                  Year {Math.ceil(semester / 2)}
                                </p>
                              </div>

                              <FiArrowRight className="shrink-0 text-gray-400 transition group-hover:translate-x-1 group-hover:text-cyan-600" />
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </HomeLayout>
  );
};

export default Departments;
