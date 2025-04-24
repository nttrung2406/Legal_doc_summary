import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const Header = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography
          variant="h6"
          component="div"
          sx={{ flexGrow: 1, cursor: 'pointer' }}
          onClick={() => navigate('/documents')}
        >
          ReadLaw
        </Typography>
        {user ? (
          <Box>
            <Button color="inherit" onClick={() => navigate('/documents')}>
              Tài liệu
            </Button>
            <Button color="inherit" onClick={handleLogout}>
              Đăng xuất
            </Button>
          </Box>
        ) : (
          <Box>
            <Button color="inherit" onClick={() => navigate('/login')}>
              Đăng nhập
            </Button>
            <Button color="inherit" onClick={() => navigate('/signup')}>
              Đăng ký
            </Button>
          </Box>
        )}
      </Toolbar>
    </AppBar>
  );
};

export default Header; 