import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import { AuthProvider } from './context/AuthContext';
import Header from './components/common/Header';
import Login from './components/Auth/Login';
import Signup from './components/Auth/Signup';
import DocumentList from './components/Document/DocumentList';
import DocumentViewer from './components/Document/DocumentViewer';
import LandingPage from './components/Landing/LandingPage';
import InfoCardList from './components/InfoCardList';
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

// Wrapper component to handle header visibility
const AppContent = () => {
  const location = useLocation();
  const isLandingPage = location.pathname === '/';

  return (
    <>
      {!isLandingPage && <Header />}
      <Routes>
        <Route path="/" element={<LandingPage />} />
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
      </Routes>
    </>
  );
};

function App() {
  const data = [
    {
      title: 'Nhà nước là gì?',
      content: 'Nhà nước là một tổ chức chính trị, xã hội có quyền lực tối cao trong phạm vi lãnh thổ nhất định và có vai trò điều hành, quản lý xã hội, duy trì trật tự và bảo vệ quyền lợi chung của mọi công dân.',
    },
    {
      title: 'Pháp luật là gì?',
      content: 'Pháp luật là một hệ thống các quy định được nhà nước ban hành hoặc thừa nhận, nhằm điều chỉnh các quan hệ xã hội, đảm bảo trật tự, công lý và bảo vệ quyền lợi của người dân.',
    },
    {
      title: 'Các hình thức vi phạm pháp luật',
      content: 'Vi phạm pháp luật có thể xảy ra dưới nhiều hình thức, bao gồm vi phạm hành chính, vi phạm hình sự, hoặc các hành vi trái pháp luật khác ảnh hưởng đến trật tự xã hội.',
    },
    {
      title: 'Trách nhiệm pháp lý là gì?',
      content: 'Trách nhiệm pháp lý là nghĩa vụ của cá nhân hoặc tổ chức phải chịu các hình thức xử lý khi có hành vi vi phạm pháp luật, từ đó đảm bảo sự công bằng và trật tự trong xã hội.',
    },
  ];
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Router>
          <AppContent />
          {/* <InfoCardList data={data} /> */}
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
