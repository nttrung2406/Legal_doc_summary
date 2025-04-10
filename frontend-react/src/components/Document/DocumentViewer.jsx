import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { documents } from '../../services/api';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  TextField,
  Button,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import { ExpandMore as ExpandMoreIcon, Send as SendIcon } from '@mui/icons-material';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

// Set up PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.mjs`;

const DocumentViewer = () => {
  const { filename } = useParams();
  const navigate = useNavigate();
  const [document, setDocument] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState(0);
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [summary, setSummary] = useState('');
  const [paragraphSummaries, setParagraphSummaries] = useState([]);
  const [chatQuery, setChatQuery] = useState('');
  const [chatMessages, setChatMessages] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [PDFUrl, setPDFUrl] = useState('');

  useEffect(() => {
    fetchDocument();
  }, [filename]);

  const fetchDocument = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const res = await fetch(`http://localhost:8000/document/${filename}`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      if (!res.ok) {
        console.error("Failed to fetch PDF:", res.status);
        setError("Document not found");
        return;
      }
      const blob = await res.blob();
      const file = new File([blob], filename, { type: 'application/pdf' });
      setDocument(file);  
    } catch (err) {
      setError('Failed to fetch document');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = async (event, newValue) => {
    setActiveTab(newValue);
    if (newValue === 1 && !summary) {
      try {
        const data = await documents.getSummary(filename);
        setSummary(data.summary);
      } catch (err) {
        setError('Failed to fetch summary');
      }
    } else if (newValue === 2 && paragraphSummaries.length === 0) {
      try {
        const data = await documents.getParagraphSummaries(filename);
        setParagraphSummaries(data.summaries);
      } catch (err) {
        setError('Failed to fetch paragraph summaries');
      }
    }
  };

  const handleChat = async () => {
    if (!chatQuery.trim()) return;

    setChatLoading(true);
    try {
      const data = await documents.chat(filename, chatQuery);
      setChatMessages(prev => [...prev, 
        { type: 'user', content: chatQuery },
        { type: 'assistant', content: data.response }
      ]);
      setChatQuery(''); // Clear the input after successful chat
    } catch (err) {
      console.error('Chat error:', err);
      setError('Failed to get chat response');
    } finally {
      setChatLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (!document) {
    return (
      <Container>
        <Alert severity="error">Document not found</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Typography variant="h4" component="h1">
          {filename}
        </Typography>
        <Button variant="outlined" onClick={() => navigate('/documents')}>
          Back to Documents
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Document
              file={document}
              onLoadSuccess={({ numPages }) => setNumPages(numPages)}
              loading={
                <Box display="flex" justifyContent="center" p={2}>
                  <CircularProgress />
                </Box>
              }
            >
              <Page
                pageNumber={pageNumber}
                width={500}
                renderTextLayer={false}
                renderAnnotationLayer={false}
              />
            </Document>
            {numPages && (
              <Box display="flex" justifyContent="center" mt={2}>
                <Button
                  disabled={pageNumber <= 1}
                  onClick={() => setPageNumber(pageNumber - 1)}
                >
                  Previous
                </Button>
                <Typography sx={{ mx: 2, py: 1 }}>
                  Page {pageNumber} of {numPages}
                </Typography>
                <Button
                  disabled={pageNumber >= numPages}
                  onClick={() => setPageNumber(pageNumber + 1)}
                >
                  Next
                </Button>
              </Box>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Tabs value={activeTab} onChange={handleTabChange}>
              <Tab label="Overall Summary" />
              <Tab label="Paragraph Summaries" />
              <Tab label="Chat" />
            </Tabs>

            <Box sx={{ mt: 2, flex: 1, display: 'flex', flexDirection: 'column' }}>
              {activeTab === 0 && (
                <Typography sx={{ flex: 1 }}>{summary || 'Loading summary...'}</Typography>
              )}

              {activeTab === 1 && (
                <Box sx={{ flex: 1, overflow: 'auto' }}>
                  {paragraphSummaries.map((summary, index) => (
                    <Accordion key={index}>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography>Paragraph {index + 1}</Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Typography>{summary}</Typography>
                      </AccordionDetails>
                    </Accordion>
                  ))}
                </Box>
              )}

              {activeTab === 2 && (
                <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                  <List sx={{ flex: 1, overflow: 'auto', mb: 2 }}>
                    {chatMessages.map((message, index) => (
                      <Box key={index}>
                        <ListItem
                          sx={{
                            justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start',
                            alignItems: 'flex-start'
                          }}
                        >
                          <Paper
                            elevation={1}
                            sx={{
                              p: 2,
                              maxWidth: '70%',
                              backgroundColor: message.type === 'user' ? 'primary.light' : 'grey.100',
                              color: message.type === 'user' ? 'white' : 'text.primary'
                            }}
                          >
                            <ListItemText
                              primary={message.content}
                              sx={{ wordBreak: 'break-word' }}
                            />
                          </Paper>
                        </ListItem>
                        <Divider />
                      </Box>
                    ))}
                  </List>
                  <Box sx={{ display: 'flex', gap: 1, mt: 'auto' }}>
                    <TextField
                      fullWidth
                      multiline
                      maxRows={3}
                      value={chatQuery}
                      onChange={(e) => setChatQuery(e.target.value)}
                      placeholder="Ask a question about the document..."
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          handleChat();
                        }
                      }}
                    />
                    <Button
                      variant="contained"
                      onClick={handleChat}
                      disabled={chatLoading || !chatQuery.trim()}
                      sx={{ minWidth: '100px' }}
                    >
                      {chatLoading ? <CircularProgress size={24} /> : <SendIcon />}
                    </Button>
                  </Box>
                </Box>
              )}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default DocumentViewer; 