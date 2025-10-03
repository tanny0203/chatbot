
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const success = await login(email, password);
      if (success) {
        navigate('/');
      } else {
        setError('Invalid email or password. Please try again.');
      }
    } catch (error) {
      setError('Login failed. Please check your connection and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-split-bg">
      <div className="login-form-panel fade-in">
        {/* Excel-style title bar */}
        <div className="excel-title-bar"></div>
        
        {/* Robot illustration */}
        <div className="robot-container">
          <div className="robot">
            <div className="robot-head">
              <div className="robot-antenna"></div>
              <div className="robot-screen">
                <div className="robot-eyes">
                  <div className="robot-eye"></div>
                  <div className="robot-eye"></div>
                </div>
              </div>
            </div>
            <div className="robot-body">
              <div className="robot-arm left"></div>
              <div className="robot-arm right"></div>
            </div>
          </div>
        </div>
        
        <div className="login-form-header">Sign in to ChatXL</div>
        <form onSubmit={handleSubmit} className="login-form">
          {error && <div className="error-message">{error}</div>}
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="Enter your email address"
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="Enter your password"
            />
          </div>
          <button type="submit" disabled={isLoading} className="auth-button">
            {isLoading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
        <div className="auth-link">
          Don't have an account? <Link to="/register">Create account</Link>
        </div>
      </div>
    </div>
  );
};

export default Login;