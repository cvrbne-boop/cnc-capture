import React, {useState} from 'react';

export default function Login({onLogin}) {
  const [username, setUsername] = useState('');
  const [loading, setLoading] = useState(false);
  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const res = await fetch('/api/v1/auth/login', {
      method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({username})
    });
    const data = await res.json();
    setLoading(false);
    if (data.access_token) {
      localStorage.setItem('token', data.access_token);
      onLogin();
    }
  };
  return (
    <form onSubmit={submit}>
      <h3>Login</h3>
      <input value={username} onChange={e=>setUsername(e.target.value)} placeholder="username" />
      <button type="submit" disabled={loading}>Login</button>
    </form>
  );
}
