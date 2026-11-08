import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/Layout/Navbar";
import Footer from "./components/Layout/Footer";
import Home from "./pages/Home";
import Input from "./pages/Input";
import Results from "./pages/Results";

export default function App() {
  return (
    <BrowserRouter>
      <div className="chaos-bg" />
      <Navbar />
      <main className="min-h-screen">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/input" element={<Input />} />
          <Route path="/results/:userId" element={<Results />} />
        </Routes>
      </main>
      <Footer />
    </BrowserRouter>
  );
}
