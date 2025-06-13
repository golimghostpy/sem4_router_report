import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import RouterForm from './pages/RouterForm';
import ReportPage from './pages/ReportPage';

function App() {
  return (
    <Router>
      <div className="app">
        <Routes>
          <Route path="/" element={<RouterForm />} />
          <Route path="/report" element={<ReportPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;