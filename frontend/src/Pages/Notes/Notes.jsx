
import React, { useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  FiArrowLeft,
  FiBookOpen,
  FiFileText,
} from "react-icons/fi";

import HomeLayout from "../../Components/Layouts/HomeLayout";
import ShowingFiles from "../../Components/ShowingFiles";

const Notes = () => {
  const { facultyId, departmentId, semester } = useParams();

  const facultyNames = {
    engineering: "Engineering",
    science: "Science",
    management: "Management",
    humanities: "Humanities",
  };

  const departmentNames = {
    cse: "Computer Science & Engineering",
    it: "Information Technology",
    civil: "Civil Engineering",
    mechanical: "Mechanical Engineering",
    electrical: "Electrical Engineering",
    physics: "Physics",
    chemistry: "Chemistry",
    mathematics: "Mathematics",
    business: "Business Administration",
    commerce: "Commerce",
    english: "English",
    economics: "Economics",
  };

  const facultyName = facultyNames[facultyId] || facultyId;
  const departmentName =
    departmentNames[departmentId] || departmentId;

  const dummyFileUrl =
    "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf";

  // Dummy data for UI testing. Replace this with backend data later.
  const [notes, setNotes] = useState(() => [
    {
      id: "note-001",
      name: "Introduction to Programming.pdf",
      size: 1024 * 1024 * 1.2,
      faculty: facultyName,
      department: departmentName,
      semester,
      fileUrl: dummyFileUrl,
      isSaved: true,
    },
    {
      id: "note-002",
      name: "Data Structures and Algorithms.pdf",
      size: 1024 * 850,
      faculty: facultyName,
      department: departmentName,
      semester,
      fileUrl: dummyFileUrl,
      isSaved: false,
    },
    {
      id: "note-003",
      name: "Database Management Systems.pdf",
      size: 1024 * 1024 * 2.4,
      faculty: facultyName,
      department: departmentName,
      semester,
      fileUrl: dummyFileUrl,
      isSaved: false,
    },
    {
      id: "note-004",
      name: "Computer Networks.pdf",
      size: 1024 * 650,
      faculty: facultyName,
      department: departmentName,
      semester,
      fileUrl: dummyFileUrl,
      isSaved: true,
    },
    {
      id: "note-005",
      name: "Operating Systems - Unit Notes.pdf",
      size: 1024 * 1024 * 1.8,
      faculty: facultyName,
      department: departmentName,
      semester,
      fileUrl: dummyFileUrl,
      isSaved: false,
    },
    {
      id: "note-006",
      name: "Previous Year Question Paper.pdf",
      size: 1024 * 420,
      faculty: facultyName,
      department: departmentName,
      semester,
      fileUrl: dummyFileUrl,
      isSaved: false,
    },
  ]);

  const [savingIds, setSavingIds] = useState({});

  // Dummy API call. Replace with your FastAPI request later.
  const mockSaveNoteApi = (noteId, shouldSave) => {
    return new Promise((resolve) => {
      setTimeout(() => {
        console.log(
          `Dummy API: ${shouldSave ? "Saved" : "Unsaved"} note`,
          noteId
        );

        resolve({
          success: true,
          id: noteId,
          isSaved: shouldSave,
        });
      }, 1000);
    });
  };

  const handleToggleSave = async (note) => {
    if (savingIds[note.id]) return;

    const nextSavedState = !note.isSaved;

    setSavingIds((previous) => ({
      ...previous,
      [note.id]: true,
    }));

    try {
      const response = await mockSaveNoteApi(
        note.id,
        nextSavedState
      );

      if (response.success) {
        setNotes((previous) =>
          previous.map((item) =>
            item.id === note.id
              ? { ...item, isSaved: response.isSaved }
              : item
          )
        );
      }
    } catch (error) {
      console.error("Failed to update saved note:", error);
    } finally {
      setSavingIds((previous) => ({
        ...previous,
        [note.id]: false,
      }));
    }
  };

  return (
    <HomeLayout>
      <div className="min-h-screen bg-gray-50 px-4 py-8 sm:px-8">
        <div className="mx-auto max-w-6xl">
          <Link
            to={`/faculty/${facultyId}`}
            className="mb-6 inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-gray-600 transition hover:bg-white hover:text-cyan-600"
          >
            <FiArrowLeft />
            Back to Departments
          </Link>

          {/* Page header */}
          <div className="mb-8 rounded-2xl border border-gray-100 bg-white p-6 shadow-inner shadow-gray-200 sm:p-8">
            <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="mb-2 text-sm font-semibold uppercase tracking-wider text-cyan-600">
                  Notes Library
                </p>

                <h1 className="text-2xl font-bold text-gray-900 sm:text-3xl">
                  Semester {semester} Notes
                </h1>

                <p className="mt-2 text-gray-500">
                  Browse, save, and access your study materials.
                </p>
              </div>

              <div className="flex shrink-0 items-center gap-3 rounded-xl bg-cyan-50 p-4">
                <div className="rounded-lg bg-white p-3 text-cyan-600 shadow-sm">
                  <FiBookOpen size={24} />
                </div>

                <div>
                  <p className="text-2xl font-bold text-gray-900">
                    {notes.length}
                  </p>
                  <p className="text-sm text-gray-500">
                    Total Files
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-6 flex flex-wrap gap-2 border-t border-gray-100 pt-5">
              <span className="rounded-full bg-cyan-50 px-3 py-1.5 text-sm font-medium text-cyan-700">
                {facultyName}
              </span>

              <span className="rounded-full bg-gray-100 px-3 py-1.5 text-sm font-medium text-gray-700">
                {departmentName}
              </span>

              <span className="rounded-full bg-gray-100 px-3 py-1.5 text-sm font-medium text-gray-700">
                Semester {semester}
              </span>
            </div>
          </div>

          {/* Files */}
          <div className="mb-5">
            <h2 className="text-xl font-bold text-gray-800">
              Available Files
            </h2>

            <p className="mt-1 text-sm text-gray-500">
              {notes.length} files available
            </p>
          </div>

          {notes.length > 0 ? (
            <div className="space-y-4">
              {notes.map((file) => (
                <ShowingFiles
                  key={file.id}
                  id={file.id}
                  name={file.name}
                  size={file.size}
                  faculty={file.faculty}
                  department={file.department}
                  fileUrl={file.fileUrl}
                  isSaved={file.isSaved}
                  isSaving={Boolean(savingIds[file.id])}
                  onToggleSave={() => handleToggleSave(file)}
                />
              ))}
            </div>
          ) : (
            <div className="rounded-2xl border border-dashed border-gray-300 bg-white px-6 py-14 text-center">
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-cyan-50 text-cyan-600">
                <FiFileText size={26} />
              </div>

              <h3 className="text-lg font-semibold text-gray-800">
                No notes available yet
              </h3>

              <p className="mt-2 text-sm text-gray-500">
                Study materials for this semester will appear here
                when they are uploaded.
              </p>
            </div>
          )}
        </div>
      </div>
    </HomeLayout>
  );
};

export default Notes;
