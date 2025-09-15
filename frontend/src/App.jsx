import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Link, useParams } from "react-router-dom";

const API_URL = "http://127.0.0.1:8000"; // backend
const categories = ["Finance", "Legal", "Technical", "HR", "General"];

// 🔹 Category Page Component
function CategoryPage({ documents }) {
  const { category } = useParams();
  const catDocs = documents.filter((doc) => doc.category === category);

  return (
    <div style={{ padding: "20px", background: "#111", color: "#fff", minHeight: "100vh" }}>
      <h1 style={{ color: "cyan" }}>{category} Documents</h1>
      <Link to="/" style={{ color: "yellow" }}>⬅ Back to Home</Link>
      <ul style={{ marginTop: "20px" }}>
        {catDocs.length > 0 ? (
          catDocs.map((doc) => (
            <li key={doc.id} style={{ marginBottom: "8px" }}>
              {doc.filename}
            </li>
          ))
        ) : (
          <p>No documents in this category</p>
        )}
      </ul>
    </div>
  );
}

// 🔹 Home Page Component
function HomePage({ file, setFile, handleUpload, output, documents, fetchDocuments }) {
  return (
    <div style={{ background: "#111", color: "#fff", minHeight: "100vh", padding: "20px" }}>
      <h1 style={{ color: "cyan" }}>KMRL Document Assistant</h1>

      {/* File Upload */}
      <input type="file" onChange={(e) => setFile(e.target.files[0])} />
      {file && <span style={{ marginLeft: "10px" }}>{file.name}</span>}

      {/* Buttons */}
      <div style={{ marginTop: "15px" }}>
        <button onClick={() => handleUpload("upload")}>Extract Text</button>
        <button onClick={() => handleUpload("summarize")}>Summarize</button>
        <button onClick={() => handleUpload("extract_entities")}>Extract Entities</button>
        <button onClick={fetchDocuments}>Fetch Documents</button>
      </div>

      {/* Output */}
      {output && (
        <pre style={{ background: "#222", padding: "10px", marginTop: "20px", color: "lime" }}>
          {output}
        </pre>
      )}

      {/* Categories Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "15px", marginTop: "30px" }}>
        {categories.map((cat) => (
          <Link
            key={cat}
            to={`/${cat}`}
            style={{
              background: "#222",
              padding: "20px",
              borderRadius: "8px",
              textDecoration: "none",
              color: "cyan",
              textAlign: "center",
            }}
          >
            <h2>{cat}</h2>
            <p style={{ color: "gray" }}>Click to view documents</p>
          </Link>
        ))}
      </div>
    </div>
  );
}

// 🔹 Main App
export default function App() {
  const [file, setFile] = useState(null);
  const [output, setOutput] = useState("");
  const [documents, setDocuments] = useState([]);

  const handleUpload = async (endpoint) => {
    if (!file) {
      alert("Please upload a file first!");
      return;
    }
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_URL}/${endpoint}/`, { method: "POST", body: formData });
    const data = await response.json();
    setOutput(JSON.stringify(data, null, 2));
    fetchDocuments(); // refresh
  };

  const fetchDocuments = async () => {
    const response = await fetch(`${API_URL}/documents/`);
    const data = await response.json();
    setDocuments(data);
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage file={file} setFile={setFile} handleUpload={handleUpload} output={output} documents={documents} fetchDocuments={fetchDocuments} />} />
        <Route path="/:category" element={<CategoryPage documents={documents} />} />
      </Routes>
    </Router>
  );
}
