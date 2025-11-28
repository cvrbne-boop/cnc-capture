import React, {useState} from 'react';
import Login from './pages/Login';
import Admin from './pages/Admin';
import Scanner from './pages/Scanner';

export default function App(){
  const [authed, setAuthed] = useState(!!localStorage.getItem('token'));
  if (!authed) return <Login onLogin={()=>setAuthed(true)} />
  return (
    <div style={{padding:20}}>
      <h1>CNC Capture — Admin / Scanner</h1>
      <div style={{display:'flex',gap:20}}>
        <div style={{flex:1}}><Admin /></div>
        <div style={{flex:1}}><Scanner /></div>
      </div>
    </div>
  );
}
