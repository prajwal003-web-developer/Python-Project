
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
import Register from './Pages/LoginRegister/Register'
import Login from './Pages/LoginRegister/Login'
import AddNote from './Pages/Authorized/AddNote'



const App = () => {
  return (
    <BrowserRouter>

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/faculty" element={<Faculties />} />
        <Route path="/faculty/:facultyId" element={<Departments/>} />
        <Route path="/faculty/:facultyId/:departmentId/:semester" element={<Notes/>} />

        <Route path="/saved" element={<SavedNotes />} />


        <Route path="/register" element={<Register/>} />

        <Route path="/login" element={<Login/>} />

        <Route path="/add" element={<AddNote/>} />
        
      </Routes>
    </BrowserRouter>
  )
}

export default App
