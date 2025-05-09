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
import ReactMarkdown from 'react-markdown';

// Set up PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.mjs`;

const DocumentViewer = () => {
  const { filename, documentId } = useParams();
  const navigate = useNavigate();
  const [document, setDocument] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState(0);
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [summary, setSummary] = useState(null);
  const [clauseList, setClauseList] = useState([]);
  const [chatQuery, setChatQuery] = useState('');
  const [chatMessages, setChatMessages] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);

  useEffect(() => {
    fetchDocument();
  }, [filename]);
  
  useEffect(() => {
    if (activeTab == 0)
    {
      fetchSummary();
    }
  }, [])
  const fetchDocument = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const res = await fetch(`http://localhost:8000/document/${filename}/${documentId}`, {
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

  const fetchSummary = async() => {
    try {
      const data = await documents.getSummary(filename, documentId);
      setSummary(data.summary);
    } catch (err) {
      setError('Failed to fetch summary');
    } 
  };

  const handleTabChange = async (event, newValue) => {
    console.log("tab changed");
    console.log(newValue);
    console.log(clauseList.length);
    setActiveTab(newValue);
    
    if (newValue === 0 && !summary) {
      try {
        const data = await documents.getSummary(filename, documentId);
        setSummary(data.summary);
      } catch (err) {
        setError('Failed to fetch summary');
      }
    } else if (newValue === 1 && clauseList.length === 0) {
      try {
        const data = await documents.extractClauses(filename, documentId);
        setClauseList(data.clauses);
      } catch (err) {
        setError('Failed to fetch paragraph summaries');
      }
    }
  };

  const handleChat = async () => {
    if (!chatQuery.trim()) return;

    setChatLoading(true);
    try {
      const data = await documents.chat(filename, documentId, chatQuery);
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

  const StyledMarkdown = ({ content }) => (
    <ReactMarkdown
      components={{
        strong: ({ node, ...props }) => (
          <span style={{ fontWeight: 'bold' }} {...props} />
        ),
        li: ({ node, ...props }) => (
          <li style={{ marginLeft: '20px' }} {...props} />
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  );

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
    <Container  maxWidth={false} sx={{ mt: 6, mb: 12 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Typography variant="h4" component="h1">
          {filename}
        </Typography>
        <Button variant="outlined" onClick={() => navigate('/documents')}>
          Tài liệu
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid justifyContent="center" container spacing={3} sx={{ width: '100%' }} >
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
                scale={1.3}
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

            <Grid item xs={12} md={6} sx={{ flex: 1 }}>
              <Paper sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <Tabs value={activeTab} onChange={handleTabChange} sx={{ width: '100%', display: 'flex', gap: 2 }}>
                <Tab label="Tóm tắt tài liệu" sx={{ flexGrow: 1, textAlign: 'center' }} />
                <Tab label="Các điều khoản/quy định" sx={{ flexGrow: 1, textAlign: 'center' }} />
                <Tab label="Hỏi đáp" sx={{ flexGrow: 1, textAlign: 'center' }} />
              </Tabs>

              <Box sx={{ mt: 2, flex: 1, display: 'flex', flexDirection: 'column', width: '100%' }}>
                {activeTab === 0 && (
                <Box sx={{ flex: 1, overflow: 'auto', maxWidth: '100%' }}>
                  {summary ? <StyledMarkdown content={summary} /> : 'Loading summary...'}
                </Box>
                )}

                {activeTab === 1 && (
                <Box sx={{ flex: 1, overflow: 'auto', maxWidth: '100%' }}>
                  {clauseList.map((clause, index) => (
                  <Accordion key={clause.title} sx={{ width: '100%' }}>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography>{clause.title}</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                    <StyledMarkdown content={clause.content} />
                    </AccordionDetails>
                  </Accordion>
                  ))}
                </Box>
                )}

              {activeTab === 2 && (
                <Box sx={{ 
                  display: 'flex', 
                  flexDirection: 'column', 
                  height: '100%',
                  width: '95%', 
                  margin: '0 auto',
                  position: 'relative'
                }}>
                  <List sx={{ 
                    flex: 1, 
                    overflow: 'auto', 
                    mb: 2,
                    height: '100%',
                    maxHeight: 'calc(100% - 100px)',
                    paddingBottom: '20px',
                    '&::-webkit-scrollbar': {
                      width: '8px',
                    },
                    '&::-webkit-scrollbar-track': {
                      background: '#f1f1f1',
                    },
                    '&::-webkit-scrollbar-thumb': {
                      background: '#888',
                      borderRadius: '4px',
                    },
                    '&::-webkit-scrollbar-thumb:hover': {
                      background: '#555',
                    },
                  }}>
                    {chatMessages.map((message, index) => (
                      <Box key={index}>
                        <ListItem
                          sx={{
                            justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start',
                            alignItems: 'flex-start',
                            py: 1,
                            px: 2
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
                            {message.type === 'user' ? (
                              <ListItemText
                                primary={message.content}
                                sx={{ wordBreak: 'break-word' }}
                              />
                            ) : (
                              <StyledMarkdown content={message.content} />
                            )}
                          </Paper>
                        </ListItem>
                        <Divider />
                      </Box>
                    ))}
                  </List>
                  <Box sx={{ 
                    display: 'flex', 
                    gap: 2, 
                    mt: 'auto',
                    backgroundColor: 'white',
                    pt: 1,
                    pb: 1,
                    borderTop: '1px solid #e0e0e0'
                  }}>
                    <TextField
                      fullWidth
                      multiline
                      maxRows={3}
                      value={chatQuery}
                      onChange={(e) => setChatQuery(e.target.value)}
                      placeholder="Hỏi gì đó về tài liệu..."
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