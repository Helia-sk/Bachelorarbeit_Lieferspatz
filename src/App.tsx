import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { CartProvider } from './contexts/CartContext';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import RestaurantLogin from './pages/RestaurantLogin';
import CustomerLogin from './pages/CustomerLogin';
import RestaurantDashboard from './pages/RestaurantDashboard';
import CustomerDashboard from './pages/CustomerDashboard';


function App() {
  return (
    <CartProvider>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Navbar />
          <main className="container mx-auto px-4 py-8">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/restaurant/login" element={<RestaurantLogin />} />
              <Route path="/customer/login" element={<CustomerLogin />} />
              <Route path="/restaurant/dashboard/*" element={<RestaurantDashboard />} />
              <Route path="/customer/dashboard/*" element={<CustomerDashboard />} />
            </Routes>
          </main>
  
        </div>
      </Router>
    </CartProvider>
  );
}

export default App;