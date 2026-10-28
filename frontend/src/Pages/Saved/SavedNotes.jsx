
import React from "react";
import { Link } from "react-router-dom";
import {
  FiBookmark,
  FiBookOpen,
  FiFileText,
  FiLogIn,
  FiArrowRight,
  FiHeart,
} from "react-icons/fi";

import HomeLayout from "../../Components/Layouts/HomeLayout";
import ShowingFiles from "../../Components/ShowingFiles";
import useUserStore from "../../Stores/useUserStore";

const SavedNotes = ({
  user = null,
  savedNotes = [],
  loading = false,
  onToggleSave = () => {},
}) => {

  const {isLoggedIn} = useUserStore()

  return (
    <HomeLayout>
      <div className="min-h-screen bg-gray-50 px-4  sm:px-8">
        <div className="mx-auto ">
          {/* Page heading */}
          <div className="mb-8 rounded-2xl border border-gray-100 bg-white p-6 shadow-inner shadow-gray-200 sm:p-8">
            <div className="flex items-center gap-4">
              <div className="rounded-xl bg-cyan-50 p-4 text-cyan-600">
                <FiBookmark size={28} />
              </div>

              <div>
                <h1 className="text-2xl font-bold text-gray-900 sm:text-3xl">
                  Saved Notes
                </h1>
                <p className="mt-2 text-sm text-gray-500 sm:text-base">
                  Keep your favorite study materials close at hand.
                </p>
              </div>
            </div>
          </div>

          {/* Loading state */}
          {loading ? (
            <div className="rounded-2xl border border-gray-100 bg-white px-6 py-16 text-center shadow-inner shadow-gray-200">
              <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-cyan-100 border-t-cyan-600" />

              <h2 className="font-semibold text-gray-800">
                Loading your saved notes...
              </h2>

              <p className="mt-2 text-sm text-gray-500">
                Just a moment while we get everything ready.
              </p>
            </div>
          ) : !isLoggedIn ? (
            /* Logged-out state */
            <div className="rounded-2xl border border-gray-100 bg-white px-6 py-12 text-center shadow-inner shadow-gray-200 sm:px-12 sm:py-16">
              <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-3xl bg-cyan-50 text-cyan-600">
                <FiBookmark size={34} />
              </div>

              <h2 className="text-xl font-bold text-gray-900 sm:text-2xl">
                Your study space is waiting!
              </h2>

              <p className="mx-auto mt-3 max-w-lg text-sm leading-6 text-gray-500 sm:text-base">
                Create a free account to save useful notes, organize
                your study materials, and find them whenever you need
                them. Your next study session starts here.
              </p>

              <div className="mt-7 flex flex-col justify-center gap-3 sm:flex-row">
                <Link
                  to="/register"
                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-cyan-600 px-6 py-3 font-semibold text-white shadow-sm transition hover:bg-cyan-700"
                >
                  <FiLogIn size={18} />
                  Create an Account
                  <FiArrowRight size={17} />
                </Link>

                <Link
                  to="/faculty"
                  className="inline-flex items-center justify-center gap-2 rounded-xl border border-gray-200 bg-white px-6 py-3 font-semibold text-gray-700 transition hover:border-cyan-200 hover:bg-cyan-50 hover:text-cyan-700"
                >
                  <FiBookOpen size={18} />
                  Explore Notes
                </Link>
              </div>

              <p className="mt-5 text-xs text-gray-400">
                Already have an account? You can sign in to access
                your saved notes.
              </p>
            </div>
          ) : savedNotes.length > 0 ? (
            /* Logged-in user with saved notes */
            <>
              <div className="mb-5 flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-xl font-bold text-gray-800">
                    Your Collection
                  </h2>
                  <p className="mt-1 text-sm text-gray-500">
                    Notes you've saved for later.
                  </p>
                </div>

                <span className="shrink-0 rounded-full bg-cyan-50 px-4 py-2 text-sm font-semibold text-cyan-700">
                  {savedNotes.length}{" "}
                  {savedNotes.length === 1 ? "Note" : "Notes"}
                </span>
              </div>

              <div className="space-y-4">
                {savedNotes.map((file) => (
                  <ShowingFiles
                    key={file.id}
                    id={file.id}
                    name={file.name}
                    size={file.size}
                    faculty={file.faculty}
                    department={file.department}
                    fileUrl={file.fileUrl}
                    isSaved={true}
                    isSaving={Boolean(file.isSaving)}
                    onToggleSave={() => onToggleSave(file)}
                  />
                ))}
              </div>

              <div className="mt-8 rounded-2xl border border-cyan-100 bg-cyan-50/60 p-5 sm:p-6">
                <div className="flex items-start gap-3">
                  <FiHeart className="mt-1 shrink-0 text-cyan-600" size={21} />
                  <div>
                    <h3 className="font-semibold text-gray-800">
                      Keep learning at your own pace
                    </h3>
                    <p className="mt-1 text-sm leading-6 text-gray-600">
                      Save useful notes as you explore different
                      departments and semesters. Your collection can
                      become your personal study library.
                    </p>
                    <Link
                      to="/faculties"
                      className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-cyan-700 hover:text-cyan-800"
                    >
                      Discover more notes
                      <FiArrowRight size={16} />
                    </Link>
                  </div>
                </div>
              </div>
            </>
          ) : (
            /* Logged-in user with no saved notes */
            <div className="rounded-2xl border border-gray-100 bg-white px-6 py-12 text-center shadow-inner shadow-gray-200 sm:px-12 sm:py-16">
              <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-3xl bg-cyan-50 text-cyan-600">
                <FiFileText size={34} />
              </div>

              <h2 className="text-xl font-bold text-gray-900 sm:text-2xl">
                Nothing saved just yet
              </h2>

              <p className="mx-auto mt-3 max-w-lg text-sm leading-6 text-gray-500 sm:text-base">
                Your saved notes will appear here. Browse your
                department, find helpful study materials, and tap
                Save to build your personal collection.
              </p>

              <Link
                to="/faculties"
                className="mt-7 inline-flex items-center justify-center gap-2 rounded-xl bg-cyan-600 px-6 py-3 font-semibold text-white shadow-sm transition hover:bg-cyan-700"
              >
                <FiBookOpen size={18} />
                Explore Study Notes
                <FiArrowRight size={17} />
              </Link>

              <p className="mt-5 text-xs text-gray-400">
                A little organization goes a long way.
              </p>
            </div>
          )}
        </div>
      </div>
    </HomeLayout>
  );
};

export default SavedNotes;
