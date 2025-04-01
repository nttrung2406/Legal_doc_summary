import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import { AuthProvider } from './context/AuthContext';
import Header from './components/common/Header';
import Login from './components/Auth/Login';
import Signup from './components/Auth/Signup';
import DocumentList from './components/Document/DocumentList';
import DocumentViewer from './components/Document/DocumentViewer';

// Create a theme instance
const theme = createTheme({
  palette: {
    primary: {
      main: '#1E3A8A',
    },
    secondary: {
      main: '#00C4B4',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
});

// Protected Route component
const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  if (!token) {
    return <Navigate to="/login" />;
  }
  return children;
};

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Router>
          <Header />
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route
              path="/documents"
              element={
                <ProtectedRoute>
                  <DocumentList />
                </ProtectedRoute>
              }
            />
            <Route
              path="/document/:filename"
              element={
                <ProtectedRoute>
                  <DocumentViewer />
                </ProtectedRoute>
              }
            />
            <Route path="/" element={<Navigate to="/documents" replace />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
