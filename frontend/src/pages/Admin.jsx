import React, {useEffect, useState} from 'react';

function fetchAuth(path, opts={}) {
  const token = localStorage.getItem('token');
  opts.headers = {...(opts.headers||{}), Authorization: `Bearer ${token}`, 'Content-Type':'application/json'};
  return fetch(path, opts).then(r=>r.json());
}

export default function Admin(){
  const [jobs, setJobs] = useState([]);
  const [machines, setMachines] = useState([]);
  const [users, setUsers] = useState([]);
  const [name, setName] = useState('');
  useEffect(()=>{ load(); },[]);
  async function load(){
    const j = await fetchAuth('/api/v1/jobs/list').catch(()=>[]);
    const m = await fetchAuth('/api/v1/machines/list').catch(()=>[]);
    setJobs(j || []);
    setMachines(m || []);
  }
  async function createJob(){
    const res = await fetchAuth('/api/v1/jobs', {method:'POST', body: JSON.stringify({name, customer:''})});
    setName('');
    load();
  }
  return (
    <div>
      <h2>Admin</h2>
      <div>
        <h4>Jobs</h4>
        <input value={name} onChange={e=>setName(e.target.value)} placeholder="Job name" />
        <button onClick={createJob}>Create</button>
        <ul>{jobs.map(j=> <li key={j.id}>{j.name} (id:{j.id})</li>)}</ul>
      </div>
    </div>
  );
}
