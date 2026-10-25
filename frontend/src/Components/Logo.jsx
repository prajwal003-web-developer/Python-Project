
import React from 'react'
import { FaBookOpen } from 'react-icons/fa'
import { Link } from 'react-router-dom'

const Logo = () => {
  return (
    <Link
      to="/"
      className="flex items-center gap-2.5 shrink-0 group"
      aria-label="ADTU Notes Home"
    >
      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-600 text-white shadow-md shadow-cyan-600/20 transition-transform group-hover:scale-105">
        <FaBookOpen className="text-xl" />
      </div>

      <div className="leading-tight">
        <h1 className="text-lg font-extrabold tracking-tight text-slate-900">
          ADTU <span className="text-cyan-600">Notes</span>
        </h1>
        <p className="mt-0.5 text-[10px] font-medium tracking-widest text-slate-500 uppercase">
          Learn. Share. Grow.
        </p>
      </div>
    </Link>
  )
}

export default Logo
