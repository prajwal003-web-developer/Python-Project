
import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  FiSearch,
  FiBookOpen,
  FiArrowRight,
  FiMonitor,
  FiCpu,
  FiLayers,
  FiUploadCloud,
  FiFileText,
  FiUsers,
  FiCompass,
  FiCheckCircle,
} from 'react-icons/fi'

import HomeLayout from '../../Components/Layouts/HomeLayout'
import { FaGraduationCap } from 'react-icons/fa'
import useFacultyStore from '../../Stores/facultiesStore'





const Home = () => {
  const [search, setSearch] = useState('')

  const {isLoading , data} = useFacultyStore()


  const handleSearch = (e) => {
    e.preventDefault()


    const query = search.trim()

    if (query) {
      window.location.href = `/search?q=${encodeURIComponent(query)}`
    } else {
      window.location.href = '/faculties'
    }
  }

  return (
    <HomeLayout>
      <main className="min-h-screen overflow-hidden bg-slate-50 text-slate-800">
        {/* Hero Section */}
        <section className="relative isolate overflow-hidden border-b border-slate-100 bg-white">
          <div className="pointer-events-none absolute -right-32 -top-28 -z-10 h-96 w-96 rounded-full bg-cyan-100/70 blur-3xl" />
          <div className="pointer-events-none absolute -bottom-32 left-0 -z-10 h-80 w-80 rounded-full bg-blue-100/50 blur-3xl" />

          <div className="mx-auto grid max-w-7xl items-center gap-12 px-4 sm:px-6  lg:grid-cols-2 lg:gap-16 lg:px-8 ">
            {/* Introduction */}
            <div>
              <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-cyan-100 bg-cyan-50 px-4 py-2 text-sm font-semibold text-cyan-800">
                <FiBookOpen className="text-lg" />
                Welcome to ADTU Notes
              </div>

              <h1 className="max-w-2xl text-4xl leading-tight font-black tracking-tight text-slate-950 sm:text-5xl lg:text-6xl">
                Everything you need to
                <span className="mt-1 block text-cyan-600">
                  learn and prepare.
                </span>
              </h1>

              <p className="mt-6 max-w-xl text-base leading-8 text-slate-600 sm:text-lg">
                ADTU Notes is a place to discover and share academic notes
                and study materials. Find resources for your program,
                semester, and subjects — all organized in one place.
              </p>

              {/* Search */}
              <form
                onSubmit={handleSearch}
                className="mt-8 flex max-w-xl items-center gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-lg shadow-slate-200/60 transition focus-within:border-cyan-400 focus-within:ring-4 focus-within:ring-cyan-500/10"
              >
                <FiSearch className="ml-2 shrink-0 text-xl text-slate-400" />

                <input
                  type="search"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search notes, subjects, programs..."
                  aria-label="Search academic notes"
                  className="min-w-0 flex-1 bg-transparent px-1 py-3 text-sm outline-none placeholder:text-slate-400 sm:text-base"
                />

                <button
                  type="submit"
                  className="shrink-0 rounded-xl bg-cyan-600 px-4 py-3 text-sm font-bold text-white transition hover:bg-cyan-700 sm:px-6"
                >
                  Search
                </button>
              </form>

              <div className="mt-5 flex flex-wrap gap-x-5 gap-y-3 text-sm text-slate-500">
                <span className="flex items-center gap-2">
                  <FiCheckCircle className="text-cyan-600" />
                  Browse without logging in
                </span>
                <span className="flex items-center gap-2">
                  <FiCheckCircle className="text-cyan-600" />
                  Organized academic resources
                </span>
              </div>

              <div className="mt-8 flex flex-wrap gap-3">
                <Link
                  to="/faculties"
                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-5 py-3.5 text-sm font-bold text-white transition hover:bg-slate-800"
                >
                  Explore Faculties
                  <FiArrowRight />
                </Link>

                <Link
                  to="/login"
                  className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-5 py-3.5 text-sm font-bold text-slate-700 transition hover:border-cyan-200 hover:bg-cyan-50 hover:text-cyan-700"
                >
                  <FiUploadCloud />
                  Contribute Notes
                </Link>
              </div>
            </div>

            {/* Visual Introduction */}
            <div className="relative mx-auto w-full max-w-lg lg:max-w-none">
              <div className="absolute -inset-4 rounded-[2rem] bg-gradient-to-br from-cyan-100 via-white to-blue-100 blur-xl" />

              <div className="relative rounded-3xl border border-slate-200 bg-white p-5 shadow-2xl shadow-slate-300/40 sm:p-7">
                <div className="flex items-center gap-4 border-b border-slate-100 pb-5">
                  <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-cyan-600 text-2xl text-white shadow-lg shadow-cyan-600/20">
                    <FiBookOpen />
                  </div>

                  <div>
                    <h2 className="text-lg font-extrabold text-slate-900 sm:text-xl">
                      Find your study materials
                    </h2>
                    <p className="mt-1 text-sm text-slate-500">
                      Follow your academic path.
                    </p>
                  </div>
                </div>

                <div className="space-y-3 py-6">
                  {[
                    {
                      number: '01',
                      title: 'Choose a faculty',
                      description: 'Start with your academic faculty.',
                    },
                    {
                      number: '02',
                      title: 'Select a department',
                      description: 'Find your department or program.',
                    },
                    {
                      number: '03',
                      title: 'Choose semester or year',
                      description: 'Navigate to your current studies.',
                    },
                    {
                      number: '04',
                      title: 'Explore subjects and notes',
                      description: 'Find available PDFs and documents.',
                    },
                  ].map((step) => (
                    <div
                      key={step.number}
                      className="flex items-start gap-4 rounded-2xl border border-slate-100 p-4 transition hover:border-cyan-200 hover:bg-cyan-50/50"
                    >
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-cyan-50 text-sm font-extrabold text-cyan-700">
                        {step.number}
                      </div>

                      <div>
                        <h3 className="text-sm font-bold text-slate-900 sm:text-base">
                          {step.title}
                        </h3>
                        <p className="mt-1 text-xs leading-5 text-slate-500 sm:text-sm">
                          {step.description}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="flex items-center gap-3 rounded-2xl bg-slate-900 p-4 text-white">
                  <FiCompass className="shrink-0 text-2xl text-cyan-300" />
                  <div>
                    <p className="text-sm font-bold">
                      Simple. Organized. Accessible.
                    </p>
                    <p className="mt-1 text-xs leading-5 text-slate-300">
                      Your resources, arranged around your curriculum.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Faculty Section */}
        <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
          <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="mb-2 text-xs font-bold tracking-[0.2em] text-cyan-700 uppercase">
                Start exploring
              </p>

              <h2 className="text-2xl font-black tracking-tight text-slate-900 sm:text-3xl">
                Explore by faculty
              </h2>

              <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-500 sm:text-base">
                Choose your faculty to discover departments, academic
                programs, semesters, subjects, and their available notes.
              </p>
            </div>

            <Link
              to="/faculties"
              className="inline-flex shrink-0 items-center gap-2 text-sm font-bold text-cyan-700 transition hover:text-cyan-900"
            >
              View all faculties <FiArrowRight />
            </Link>
          </div>

          { !!!isLoading &&
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {data?.map((faculty) => {
              const Icon = FaGraduationCap
              return (
                <Link
                  key={faculty?.name}
                  to={`/faculty/${faculty?.slug}`}
                  className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition duration-300 hover:-translate-y-1 hover:border-cyan-200 hover:shadow-xl hover:shadow-cyan-900/5 sm:p-6"
                >
                  <div className="flex items-center justify-between">
                    <div
                      className={`flex h-12 w-12 items-center justify-center rounded-xl text-2xl ${faculty.color}`}
                    >
                      <Icon />
                    </div>

                    <FiArrowRight className="text-lg text-slate-300 transition group-hover:translate-x-1 group-hover:text-cyan-700" />
                  </div>

                  <h3 className="mt-5 text-lg font-bold text-slate-900 transition group-hover:text-cyan-700">
                    {faculty?.name}
                  </h3>


                  <div className="mt-5 border-t border-slate-100 pt-4 text-xs font-semibold text-slate-500">
                    Explore academic resources
                  </div>
                </Link>
              )
            })}
          </div>
          }

          <p className="mt-4 text-xs leading-5 text-slate-400">
            Faculty cards are examples. Replace them with the actual faculties
            and programs supported by your platform.
          </p>
        </section>

        {/* How it works */}
        <section className="border-y border-slate-200 bg-white">
          <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
            <div className="mx-auto mb-10 max-w-2xl text-center">
              <p className="mb-2 text-xs font-bold tracking-[0.2em] text-cyan-700 uppercase">
                How it works
              </p>
              <h2 className="text-2xl font-black tracking-tight text-slate-900 sm:text-3xl">
                Find the right notes in a few steps
              </h2>
              <p className="mt-3 text-sm leading-7 text-slate-500 sm:text-base">
                No complicated navigation. Just follow your academic structure.
              </p>
            </div>

            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {[
                {
                  number: '01',
                  title: 'Faculty',
                  description: 'Choose the faculty your program belongs to.',
                },
                {
                  number: '02',
                  title: 'Department',
                  description: 'Select your department or academic program.',
                },
                {
                  number: '03',
                  title: 'Semester / Year',
                  description: 'Pick the semester or year you are studying.',
                },
                {
                  number: '04',
                  title: 'Subject & Notes',
                  description: 'Open a subject and access its available materials.',
                },
              ].map((item) => (
                <div key={item.number} className="relative">
                  <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-cyan-50 text-sm font-black text-cyan-700">
                    {item.number}
                  </div>
                  <h3 className="font-bold text-slate-900">{item.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-500">
                    {item.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Contribute Section */}
        <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
          <div className="relative overflow-hidden rounded-3xl bg-slate-900 px-6 py-10 sm:px-10 sm:py-14 lg:px-14">
            <div className="pointer-events-none absolute -right-16 -top-20 h-72 w-72 rounded-full bg-cyan-500/20 blur-3xl" />

            <div className="relative flex flex-col gap-8 sm:flex-row sm:items-center sm:justify-between">
              <div className="max-w-2xl">
                <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-semibold text-cyan-300">
                  <FiUsers />
                  Contribute to the community
                </div>

                <h2 className="text-2xl leading-tight font-black text-white sm:text-3xl lg:text-4xl">
                  Have useful notes? Share them.
                </h2>

                <p className="mt-4 text-sm leading-7 text-slate-300 sm:text-base">
                  Help fellow students by contributing notes and study
                  materials. Log in to upload resources and make learning
                  easier for everyone.
                </p>
              </div>

              <div className="flex shrink-0 flex-col gap-3 sm:min-w-44">
                <Link
                  to="/login"
                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-cyan-500 px-6 py-3.5 text-sm font-bold text-white transition hover:bg-cyan-400"
                >
                  <FiUploadCloud />
                  Upload Notes
                </Link>

                <p className="text-center text-xs text-slate-400">
                  Login required to contribute
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t border-slate-200 bg-white">
          <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-7 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
            <Link to="/" className="text-base font-extrabold text-slate-900">
              ADTU <span className="text-cyan-600">Notes</span>
            </Link>

            <p className="text-sm text-slate-500">
              Academic resources, organized for students.
            </p>

            <Link
              to="/faculties"
              className="text-sm font-semibold text-slate-600 transition hover:text-cyan-700"
            >
              Explore Faculties
            </Link>
          </div>
        </footer>
      </main>
    </HomeLayout>
  )
}

export default Home
