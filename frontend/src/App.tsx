import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Login from './Login';
import FileUpload from './FileUpload';
import MappingPage from './MappingPage';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/upload" element={<FileUpload />} />
        <Route path="/mapping" element={<MappingPage />} />
      </Routes>
    </Router>
  );
}

export default App;
