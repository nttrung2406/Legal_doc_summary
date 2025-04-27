import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { documents } from '../../services/api';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Box,
  CircularProgress,
  Alert,
} from '@mui/material';
import { Upload as UploadIcon } from '@mui/icons-material';
// import { pdfjs } from 'react-pdf';
// import workerSrc from 'pdfjs-dist/build/pdf.worker.entry';

// pdfjs.GlobalWorkerOptions.workerSrc = workerSrc;

const handleRename = async (id) => {
  const newName = prompt('Enter the new name for the document:');
  if (!newName) return;

  try {
    await documents.rename(id, newName);
    await fetchDocuments();
  } catch (err) {
    setError('Failed to rename document');
  }
};

const handleDelete = async (filename, documentId) => {
  if (!window.confirm('Are you sure you want to delete this document?')) return;

  try {
    await documents.deleteDocument(filename, documentId);
    await fetchDocuments();
  } catch (err) {
    setError('Failed to delete document');
  }
};
const DocumentList = () => {
  const navigate = useNavigate();
  const [userDocuments, setUserDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const data = await documents.list();
      setUserDocuments(data);
    } catch (err) {
      setError('Failed to fetch documents');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.name.endsWith('.pdf')) {
      setError('Only PDF files are allowed');
      return;
    }

    setUploading(true);
    try {
      await documents.upload(file);
      await fetchDocuments();
    } catch (err) {
      setError('Failed to upload document');
    } finally {
      setUploading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Typography variant="h4" component="h1">
          Your Documents
        </Typography>
        <Button
          variant="contained"
          component="label"
          startIcon={<UploadIcon />}
          disabled={uploading}
        >
          Upload PDF
          <input
            type="file"
            hidden
            accept=".pdf"
            onChange={handleFileUpload}
          />
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {userDocuments.map((doc) => (
          <Grid item xs={12} sm={6} md={4} key={doc.filename}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                cursor: 'pointer',
                '&:hover': {
                  boxShadow: 6,
                },
              }}
            >
              <CardContent>
                <Typography
                  variant="h6"
                  component="h2"
                  gutterBottom
                  onClick={() => navigate(`/document/${doc.filename}/${doc.id}`)}
                >
                  {doc.filename}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Uploaded on: {new Date(doc.created_at).toLocaleDateString()}
                </Typography>
              </CardContent>
              <Box display="flex" justifyContent="flex-end" p={2}>
                <Button
                  size="small"
                  variant="outlined"
                  color="error"
                  onClick={() => handleDelete(doc.filename, doc.id)}
                >
                  Delete
                </Button>
              </Box>
            </Card>
          </Grid>
        ))}
      </Grid>

      {userDocuments.length === 0 && !loading && (
        <Box textAlign="center" mt={4}>
          <Typography variant="h6" color="text.secondary">
            No documents uploaded yet
          </Typography>
        </Box>
      )}
    </Container>
  );

  
};

export default DocumentList; 