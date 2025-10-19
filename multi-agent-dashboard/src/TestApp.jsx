// src/TestApp.jsx
import React from 'react';
import './App.css';

function TestApp() {
  return (
    <div style={{ 
      minHeight: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      backgroundColor: '#f0f4f8'
    }}>
      <div style={{
        backgroundColor: 'white',
        padding: '2rem',
        borderRadius: '0.5rem',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        maxWidth: '500px',
        width: '100%',
        textAlign: 'center'
      }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '1rem' }}>
          Multi-Agent E-commerce Platform
        </h1>
        <p style={{ color: '#4b5563', marginBottom: '1.5rem' }}>
          This is a test page to verify that React rendering is working correctly.
        </p>
        <div>
          <button style={{
            backgroundColor: '#3b82f6',
            color: 'white',
            padding: '0.5rem 1rem',
            borderRadius: '0.25rem',
            border: 'none',
            cursor: 'pointer'
          }}>
            Test Button
          </button>
        </div>
      </div>
    </div>
  );
}

export default TestApp;
