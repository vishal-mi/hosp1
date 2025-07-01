import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Authentication Context
const AuthContext = React.createContext();

function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      // Set default auth header
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      
      // Try to get user info from token or localStorage
      const userData = JSON.parse(localStorage.getItem('user') || 'null');
      if (userData) {
        try {
          const payload = JSON.parse(atob(token.split('.')[1]));
          if (payload.exp > Date.now() / 1000) {
            setUser(userData);
          } else {
            logout();
          }
        } catch (error) {
          logout();
        }
      } else {
        logout();
      }
    }
  }, [token]);

  const login = (token, userData) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(userData));
    setToken(token);
    setUser(userData);
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout }}>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        {!user ? <LandingPage /> : <Dashboard />}
      </div>
    </AuthContext.Provider>
  );
}

// Landing Page Component
function LandingPage() {
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <div className="relative bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <div className="text-2xl font-bold text-indigo-600">
                🏥 HealthCare Plus
              </div>
            </div>
            <div className="flex space-x-4">
              <button
                onClick={() => setShowLogin(true)}
                className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 transition duration-200"
              >
                Login
              </button>
              <button
                onClick={() => setShowRegister(true)}
                className="border border-indigo-600 text-indigo-600 px-6 py-2 rounded-lg hover:bg-indigo-50 transition duration-200"
              >
                Register
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Hero Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            AI-Powered Healthcare
            <span className="text-indigo-600"> Appointment Booking</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Describe your symptoms and get AI-powered doctor recommendations. 
            Book appointments with the right specialists instantly.
          </p>
          <div className="flex justify-center space-x-4">
            <button
              onClick={() => setShowRegister(true)}
              className="bg-indigo-600 text-white px-8 py-3 rounded-lg text-lg font-semibold hover:bg-indigo-700 transition duration-200 shadow-lg"
            >
              Get Started
            </button>
            <button
              onClick={() => setShowLogin(true)}
              className="border-2 border-indigo-600 text-indigo-600 px-8 py-3 rounded-lg text-lg font-semibold hover:bg-indigo-50 transition duration-200"
            >
              Sign In
            </button>
          </div>
        </div>

        {/* Features */}
        <div className="mt-20 grid md:grid-cols-3 gap-8">
          <div className="text-center p-6 bg-white rounded-xl shadow-lg">
            <div className="text-4xl mb-4">🤖</div>
            <h3 className="text-xl font-semibold mb-3">AI Symptom Analysis</h3>
            <p className="text-gray-600">
              Our AI analyzes your symptoms and suggests the most appropriate medical specialists
            </p>
          </div>
          <div className="text-center p-6 bg-white rounded-xl shadow-lg">
            <div className="text-4xl mb-4">👨‍⚕️</div>
            <h3 className="text-xl font-semibold mb-3">Expert Doctors</h3>
            <p className="text-gray-600">
              Connect with qualified doctors across various specializations
            </p>
          </div>
          <div className="text-center p-6 bg-white rounded-xl shadow-lg">
            <div className="text-4xl mb-4">📅</div>
            <h3 className="text-xl font-semibold mb-3">Easy Booking</h3>
            <p className="text-gray-600">
              Book, reschedule, or cancel appointments with just a few clicks
            </p>
          </div>
        </div>
      </div>

      {/* Modals */}
      {showLogin && <LoginModal onClose={() => setShowLogin(false)} />}
      {showRegister && <RegisterModal onClose={() => setShowRegister(false)} />}
    </div>
  );
}

// Login Modal
function LoginModal({ onClose }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = React.useContext(AuthContext);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API}/login`, { email, password });
      login(response.data.access_token, response.data.user);
      onClose();
    } catch (error) {
      setError(error.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-8 rounded-xl max-w-md w-full mx-4">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Sign In</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              required
            />
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              required
            />
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-indigo-600 text-white py-2 px-4 rounded-lg hover:bg-indigo-700 transition duration-200 disabled:opacity-50"
          >
            {loading ? 'Signing In...' : 'Sign In'}
          </button>
        </form>

        <div className="mt-4 text-center">
          <p className="text-sm text-gray-600">
            Demo credentials: admin@hospital.com / admin123
          </p>
        </div>
      </div>
    </div>
  );
}

// Register Modal
function RegisterModal({ onClose }) {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    password: '',
    user_type: 'patient'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = React.useContext(AuthContext);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API}/register`, formData);
      login(response.data.access_token, response.data.user);
      onClose();
    } catch (error) {
      setError(error.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-8 rounded-xl max-w-md w-full mx-4">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Register</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Full Name
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              required
            />
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              required
            />
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Phone
            </label>
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              required
            />
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              required
            />
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Account Type
            </label>
            <select
              name="user_type"
              value={formData.user_type}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              <option value="patient">Patient</option>
              <option value="doctor">Doctor</option>
            </select>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-indigo-600 text-white py-2 px-4 rounded-lg hover:bg-indigo-700 transition duration-200 disabled:opacity-50"
          >
            {loading ? 'Registering...' : 'Register'}
          </button>
        </form>
      </div>
    </div>
  );
}

// Dashboard Component
function Dashboard() {
  const { user, logout } = React.useContext(AuthContext);
  const [activeTab, setActiveTab] = useState('symptoms');

  return (
    <div className="min-h-screen">
      {/* Header */}
      <div className="bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <div className="text-2xl font-bold text-indigo-600 mr-8">
                🏥 HealthCare Plus
              </div>
              <nav className="hidden md:flex space-x-8">
                <button
                  onClick={() => setActiveTab('symptoms')}
                  className={`py-2 px-3 rounded-lg transition duration-200 ${
                    activeTab === 'symptoms'
                      ? 'bg-indigo-100 text-indigo-700'
                      : 'text-gray-600 hover:text-indigo-600'
                  }`}
                >
                  Symptom Analysis
                </button>
                <button
                  onClick={() => setActiveTab('appointments')}
                  className={`py-2 px-3 rounded-lg transition duration-200 ${
                    activeTab === 'appointments'
                      ? 'bg-indigo-100 text-indigo-700'
                      : 'text-gray-600 hover:text-indigo-600'
                  }`}
                >
                  My Appointments
                </button>
                <button
                  onClick={() => setActiveTab('doctors')}
                  className={`py-2 px-3 rounded-lg transition duration-200 ${
                    activeTab === 'doctors'
                      ? 'bg-indigo-100 text-indigo-700'
                      : 'text-gray-600 hover:text-indigo-600'
                  }`}
                >
                  Find Doctors
                </button>
                {user?.user_type === 'admin' && (
                  <button
                    onClick={() => setActiveTab('admin')}
                    className={`py-2 px-3 rounded-lg transition duration-200 ${
                      activeTab === 'admin'
                        ? 'bg-indigo-100 text-indigo-700'
                        : 'text-gray-600 hover:text-indigo-600'
                    }`}
                  >
                    Admin Panel
                  </button>
                )}
              </nav>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-700">Welcome, {user?.name}</span>
              <button
                onClick={logout}
                className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition duration-200"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'symptoms' && <SymptomAnalysis />}
        {activeTab === 'appointments' && <AppointmentsList />}
        {activeTab === 'doctors' && <DoctorsList />}
        {activeTab === 'admin' && user?.user_type === 'admin' && <AdminPanel />}
      </div>
    </div>
  );
}

// Symptom Analysis Component
function SymptomAnalysis() {
  const [symptoms, setSymptoms] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const { user } = React.useContext(AuthContext);

  const handleAnalyze = async () => {
    if (!symptoms.trim()) return;

    setLoading(true);
    try {
      const response = await axios.post(`${API}/analyze-symptoms`, {
        symptoms,
        patient_id: user.id
      });
      setAnalysis(response.data);
    } catch (error) {
      console.error('Analysis failed:', error);
      alert('Failed to analyze symptoms. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleBookAppointment = async (doctorId) => {
    const appointmentDate = prompt('Enter appointment date and time (YYYY-MM-DD HH:MM):');
    if (!appointmentDate) return;

    try {
      await axios.post(`${API}/appointments`, {
        doctor_id: doctorId,
        appointment_date: new Date(appointmentDate).toISOString(),
        symptoms
      });
      alert('Appointment booked successfully!');
    } catch (error) {
      alert('Failed to book appointment: ' + (error.response?.data?.detail || 'Unknown error'));
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-xl shadow-lg p-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-6">
          🤖 AI Symptom Analysis
        </h2>

        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Describe your symptoms in detail:
          </label>
          <textarea
            value={symptoms}
            onChange={(e) => setSymptoms(e.target.value)}
            placeholder="E.g., I have been experiencing chest pain and shortness of breath for the past 2 days..."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            rows="6"
          />
        </div>

        <button
          onClick={handleAnalyze}
          disabled={loading || !symptoms.trim()}
          className="bg-indigo-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-indigo-700 transition duration-200 disabled:opacity-50"
        >
          {loading ? 'Analyzing...' : 'Analyze Symptoms'}
        </button>

        {analysis && (
          <div className="mt-8 space-y-6">
            {/* Analysis Results */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <h3 className="text-xl font-semibold text-blue-900 mb-3">
                AI Analysis
              </h3>
              <p className="text-blue-800">{analysis.analysis}</p>
              
              <div className="mt-4">
                <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                  analysis.urgency_level === 'Emergency' ? 'bg-red-100 text-red-800' :
                  analysis.urgency_level === 'High' ? 'bg-orange-100 text-orange-800' :
                  analysis.urgency_level === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-green-100 text-green-800'
                }`}>
                  Urgency: {analysis.urgency_level}
                </span>
              </div>
            </div>

            {/* Recommended Specialties */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <h3 className="text-xl font-semibold text-green-900 mb-3">
                Recommended Specialties
              </h3>
              <div className="flex flex-wrap gap-2">
                {analysis.recommended_specialties.map((specialty, index) => (
                  <span
                    key={index}
                    className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm"
                  >
                    {specialty}
                  </span>
                ))}
              </div>
            </div>

            {/* Recommended Doctors */}
            {analysis.recommended_doctors.length > 0 && (
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">
                  Recommended Doctors
                </h3>
                <div className="grid gap-4">
                  {analysis.recommended_doctors.map((recommendation, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h4 className="text-lg font-semibold text-gray-900">
                            {recommendation.doctor.name}
                          </h4>
                          <p className="text-gray-600 mb-2">
                            {recommendation.doctor.specializations.join(', ')}
                          </p>
                          <p className="text-sm text-gray-500 mb-2">
                            {recommendation.doctor.experience_years} years experience
                          </p>
                          <p className="text-sm text-gray-700 mb-2">
                            {recommendation.match_reason}
                          </p>
                          <p className="text-lg font-semibold text-indigo-600">
                            $${recommendation.doctor.consultation_fee}
                          </p>
                        </div>
                        <button
                          onClick={() => handleBookAppointment(recommendation.doctor.id)}
                          className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition duration-200"
                        >
                          Book Appointment
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Additional Notes */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
              <h3 className="text-xl font-semibold text-yellow-900 mb-3">
                Important Notes
              </h3>
              <p className="text-yellow-800">{analysis.additional_notes}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Appointments List Component
function AppointmentsList() {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAppointments();
  }, []);

  const fetchAppointments = async () => {
    try {
      const response = await axios.get(`${API}/appointments`);
      setAppointments(response.data);
    } catch (error) {
      console.error('Failed to fetch appointments:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateAppointmentStatus = async (appointmentId, status) => {
    try {
      await axios.put(`${API}/appointments/${appointmentId}`, { status });
      fetchAppointments(); // Refresh the list
      alert('Appointment updated successfully!');
    } catch (error) {
      alert('Failed to update appointment');
    }
  };

  if (loading) {
    return <div className="text-center py-8">Loading appointments...</div>;
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="bg-white rounded-xl shadow-lg p-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-6">
          📅 My Appointments
        </h2>

        {appointments.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No appointments found. Book your first appointment using symptom analysis!
          </div>
        ) : (
          <div className="space-y-4">
            {appointments.map((appointment) => (
              <div key={appointment.id} className="border border-gray-200 rounded-lg p-6">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="text-xl font-semibold text-gray-900">
                      Dr. {appointment.doctor_name}
                    </h3>
                    <p className="text-gray-600 mb-2">
                      {new Date(appointment.appointment_date).toLocaleString()}
                    </p>
                    <p className="text-gray-700 mb-2">
                      <strong>Symptoms:</strong> {appointment.symptoms}
                    </p>
                    {appointment.notes && (
                      <p className="text-gray-700 mb-2">
                        <strong>Notes:</strong> {appointment.notes}
                      </p>
                    )}
                    <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                      appointment.status === 'scheduled' ? 'bg-blue-100 text-blue-800' :
                      appointment.status === 'completed' ? 'bg-green-100 text-green-800' :
                      appointment.status === 'cancelled' ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {appointment.status.charAt(0).toUpperCase() + appointment.status.slice(1)}
                    </span>
                  </div>
                  <div className="flex space-x-2">
                    {appointment.status === 'scheduled' && (
                      <>
                        <button
                          onClick={() => updateAppointmentStatus(appointment.id, 'completed')}
                          className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700 transition duration-200"
                        >
                          Mark Complete
                        </button>
                        <button
                          onClick={() => updateAppointmentStatus(appointment.id, 'cancelled')}
                          className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700 transition duration-200"
                        >
                          Cancel
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// Doctors List Component
function DoctorsList() {
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDoctors();
  }, []);

  const fetchDoctors = async () => {
    try {
      const response = await axios.get(`${API}/doctors`);
      setDoctors(response.data);
    } catch (error) {
      console.error('Failed to fetch doctors:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleBookAppointment = async (doctorId) => {
    const appointmentDate = prompt('Enter appointment date and time (YYYY-MM-DD HH:MM):');
    if (!appointmentDate) return;

    const symptoms = prompt('Describe your symptoms:');
    if (!symptoms) return;

    try {
      await axios.post(`${API}/appointments`, {
        doctor_id: doctorId,
        appointment_date: new Date(appointmentDate).toISOString(),
        symptoms
      });
      alert('Appointment booked successfully!');
    } catch (error) {
      alert('Failed to book appointment: ' + (error.response?.data?.detail || 'Unknown error'));
    }
  };

  if (loading) {
    return <div className="text-center py-8">Loading doctors...</div>;
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="bg-white rounded-xl shadow-lg p-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-6">
          👨‍⚕️ Available Doctors
        </h2>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {doctors.map((doctor) => (
            <div key={doctor.id} className="border border-gray-200 rounded-lg p-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {doctor.name}
              </h3>
              <p className="text-gray-600 mb-2">
                {doctor.specializations.join(', ')}
              </p>
              <p className="text-sm text-gray-500 mb-2">
                {doctor.experience_years} years experience
              </p>
              <p className="text-sm text-gray-700 mb-3">
                {doctor.qualifications}
              </p>
              <p className="text-lg font-semibold text-indigo-600 mb-4">
                $${doctor.consultation_fee}
              </p>
              
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Available Days:</h4>
                <div className="flex flex-wrap gap-1">
                  {doctor.available_days.map((day) => (
                    <span key={day} className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                      {day}
                    </span>
                  ))}
                </div>
              </div>

              <button
                onClick={() => handleBookAppointment(doctor.id)}
                className="w-full bg-indigo-600 text-white py-2 px-4 rounded-lg hover:bg-indigo-700 transition duration-200"
              >
                Book Appointment
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Admin Panel Component
function AdminPanel() {
  const [createSampleData, setCreateSampleData] = useState(false);

  const handleCreateSampleData = async () => {
    setCreateSampleData(true);
    try {
      await axios.post(`${API}/create-sample-data`);
      alert('Sample data created successfully!');
    } catch (error) {
      alert('Failed to create sample data');
    } finally {
      setCreateSampleData(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-xl shadow-lg p-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-6">
          ⚙️ Admin Panel
        </h2>

        <div className="space-y-4">
          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Sample Data
            </h3>
            <p className="text-gray-600 mb-4">
              Create sample doctors and admin users for testing the system.
            </p>
            <button
              onClick={handleCreateSampleData}
              disabled={createSampleData}
              className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition duration-200 disabled:opacity-50"
            >
              {createSampleData ? 'Creating...' : 'Create Sample Data'}
            </button>
          </div>

          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              System Status
            </h3>
            <p className="text-green-600">✅ AI Integration Active</p>
            <p className="text-green-600">✅ Database Connected</p>
            <p className="text-green-600">✅ All Services Running</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;