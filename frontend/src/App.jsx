
import React, { useEffect, useState } from 'react'
import {
  BrowserRouter,
  Routes,
  Route,
  Link
} from 'react-router-dom'

import { ToastContainer, toast } from 'react-toastify';
import Home from './Pages/Home/page'
import Faculties from './Pages/Faculty/Faculties'
import Departments from './Pages/Department/Departments'
import Notes from './Pages/Notes/Notes'
import SavedNotes from './Pages/Saved/SavedNotes'
import Register from './Pages/LoginRegister/Register'
import Login from './Pages/LoginRegister/Login'
import AddNote from './Pages/Authorized/AddNote'
import useUserStore from './Stores/useUserStore'
import api from './Lib/api';
import Profile from './Pages/Profile';
import useFacultyStore from './Stores/facultiesStore';
import Loading from './Components/Loading';
import Search from './Pages/Search/Search';
import ComingSoon from './Components/NearFuture';
import MyNotes from './Pages/Notes/MyNotes';



const App = () => {

  const {  setIsLoggedIn , setUser} = useUserStore()

  const getData = async ()=>{
    try {
      const response = await api.get('/auth/me')
      const data = response.data
      setIsLoggedIn(true)
      setUser(data)
    } catch (error) {
      console.log(error);
    }
  }

  const {loading , setLoading  , setData } = useFacultyStore()
  const [loadingPage, setloadingPage] = useState(true);
  const getFaculties = async ()=>{
    try {
      setLoading(true)
      setloadingPage(true)
      const res = await api.get('/faculties')
      const data = res.data
      // console.log("home" , data);
      setData(data);
    } catch (error) {
      console.log(error);
    }
    finally{
      setLoading(false)
      setloadingPage(false)
    }
  }

  useEffect(()=>{
    getData()
    getFaculties()
  },[])

  if(loadingPage){
    return <Loading/>
  }
  return (
    <>
    <BrowserRouter>
  
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/faculty" element={<Faculties />} />
        <Route path="/faculty/:facultyId" element={<Departments/>} />
        <Route path="/faculty/:facultyId/:departmentId/:semester" element={<Notes/>} />

        <Route path="/saved" element={<ComingSoon />} />


        <Route path="/register" element={<Register/>} />

        <Route path="/login" element={<Login/>} />

        <Route path="/add" element={<AddNote/>} />
        <Route path="/my-notes" element={<MyNotes/>} />

        <Route path="/profile" element={<Profile/>} />

        <Route path="/search" element={<Search />} />

        
      </Routes>
      
    </BrowserRouter>
     <ToastContainer/>
    </>
  )
}

export default App
