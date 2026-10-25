
import React, { useEffect } from "react";
import { Link } from "react-router-dom";
import {
  FiArrowRight,
  FiBookOpen,
  
  FiRefreshCw,
} from "react-icons/fi";
import useFacultyStore from "../../Stores/facultiesStore";
import HomeLayout from "../../Components/Layouts/HomeLayout";
import Loading from "../../Components/Loading";
import { FaGraduationCap } from "react-icons/fa";



const Faculties = () => {
  const {
    data,
    setData,
    isFetched,
    setIsFetched,
    loading,
    setLoading,
    error,
    setError,
  } = useFacultyStore();

  // Temporary dummy data; replace with your API response later.
  const dummyFaculties = [
    {
      id: "engineering",
      name: "Faculty of Engineering",
      description: "Engineering departments and study materials.",
      departments: [
        { id: "cse", name: "Computer Science Engineering" },
        { id: "it", name: "Information Technology" },
        { id: "civil", name: "Civil Engineering" },
        { id: "mechanical", name: "Mechanical Engineering" },
        { id: "electrical", name: "Electrical Engineering" },
      ],
    },
    {
      id: "science",
      name: "Faculty of Science",
      description: "Science departments and academic resources.",
      departments: [
        { id: "physics", name: "Physics" },
        { id: "chemistry", name: "Chemistry" },
        { id: "mathematics", name: "Mathematics" },
      ],
    },
    {
      id: "management",
      name: "Faculty of Management",
      description: "Management and business study materials.",
      departments: [
        { id: "business", name: "Business Administration" },
        { id: "commerce", name: "Commerce" },
      ],
    },
    {
      id: "humanities",
      name: "Faculty of Humanities",
      description: "Humanities departments and study resources.",
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
      // Simulate an API request and loading effect.
      await new Promise((resolve) => setTimeout(resolve, 1200));

      // Later, replace this with your actual API call:
      // const response = await axios.get("/api/faculties");
      // setData(response.data);

      setData(dummyFaculties);
      setIsFetched(true);
    } catch (err) {
      setError("Failed to load faculties. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!isFetched) {
      fetchFaculties();
    }
  }, [isFetched]);

  return (
    <HomeLayout>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <section className="border-b border-gray-100 bg-white">
          <div className="mx-auto max-w-7xl px-4  sm:px-6 lg:px-8">
            <p className="text-sm font-bold uppercase tracking-widest text-cyan-600">
              ADTU Notes
            </p>

            <h1 className="mt-3 text-3xl font-extrabold tracking-tight text-gray-900 sm:text-4xl">
              Explore Faculties
            </h1>

            <p className="mt-3 max-w-2xl text-sm leading-6 text-gray-500 sm:text-base">
              Choose your faculty to explore departments, semesters, subjects,
              and academic notes in one place.
            </p>
          </div>
        </section>

        {/* Content */}
        <section className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
          {loading ? (
            <Loading message="Loading faculties..." />
          ) : error ? (
            <div className="rounded-2xl border border-red-100 bg-white p-8 text-center">
              <p className="font-semibold text-red-600">{error}</p>

              <button
                onClick={fetchFaculties}
                className="mt-4 inline-flex items-center gap-2 rounded-xl bg-cyan-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-cyan-700"
              >
                <FiRefreshCw size={16} />
                Try again
              </button>
            </div>
          ) : data.length === 0 ? (
            <div className="rounded-2xl border border-gray-200 bg-white p-10 text-center">
              <FaGraduationCap
                size={36}
                className="mx-auto text-gray-400"
              />
              <h2 className="mt-4 font-bold text-gray-800">
                No faculties found
              </h2>
              <p className="mt-2 text-sm text-gray-500">
                No faculties are available right now.
              </p>
            </div>
          ) : (
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {data.map((faculty, index) => (
                <Link
                  key={faculty.id}
                  to={`/faculty/${faculty.id}`}
                  className="group rounded-2xl border border-gray-200 bg-white p-6 shadow-sm transition duration-300 hover:-translate-y-1 hover:border-cyan-200 hover:shadow-lg"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-50 text-cyan-700 transition group-hover:bg-cyan-600 group-hover:text-white">
                      <FaGraduationCap size={25} />
                    </div>

                    <span className="text-sm font-semibold text-gray-300">
                      {String(index + 1).padStart(2, "0")}
                    </span>
                  </div>

                  <h2 className="mt-5 text-lg font-bold text-gray-900 transition group-hover:text-cyan-700">
                    {faculty.name}
                  </h2>

                  <p className="mt-2 min-h-10 text-sm leading-6 text-gray-500">
                    {faculty.description}
                  </p>

                  <div className="mt-5 flex items-center justify-between border-t border-gray-100 pt-4">
                    <span className="flex items-center gap-2 text-sm text-gray-500">
                      <FiBookOpen size={16} />
                      {faculty.departments.length} departments
                    </span>

                    <span className="flex items-center gap-1 text-sm font-semibold text-cyan-700">
                      Explore
                      <FiArrowRight className="transition group-hover:translate-x-1" />
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </section>
      </div>
    </HomeLayout>
  );
};

export default Faculties;
