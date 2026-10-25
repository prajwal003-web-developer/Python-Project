import React from 'react'
import Navabar from '../Navabar'

const HomeLayout = ( {children}) => {
  return (
    <main>
        <Navabar/>
       <section className='py-24'>
         {children}
       </section>
    </main>
  )
}

export default HomeLayout