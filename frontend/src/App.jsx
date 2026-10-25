
import React from 'react'
import {
  BrowserRouter,
  Routes,
  Route,
  Link
} from 'react-router-dom'
import Home from './Pages/Home/page'
import Faculties from './Pages/Faculty/Faculties'
import Departments from './Pages/Department/Departments'
import Notes from './Pages/Notes/Notes'
import SavedNotes from './Pages/Saved/SavedNotes'



const App = () => {
  return (
    <BrowserRouter>

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/faculty" element={<Faculties />} />
        <Route path="/faculty/:facultyId" element={<Departments/>} />
        <Route path="/faculty/:facultyId/:departmentId/:semester" element={<Notes/>} />

        <Route path="/saved" element={<SavedNotes />} />




        
      </Routes>
    </BrowserRouter>
  )
}

export default App
