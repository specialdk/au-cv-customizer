import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Button,
  Box,
  TextField,
  Grid,
  Card,
  CardContent,
  CardActions,
  Divider,
  List,
  ListItem,
  ListItemText,
  Checkbox,
  IconButton
} from '@mui/material';
import { 
  UploadFile as UploadIcon, 
  Work as WorkIcon,
  Delete as DeleteIcon 
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import * as api from '../services/api';
import NavBar from '../components/NavBar';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [jobUrl, setJobUrl] = useState('');
  const [jobTitle, setJobTitle] = useState('');
  const [company, setCompany] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [uploadedCV, setUploadedCV] = useState<{
    id: number;
    name: string;
    uploadTime: string;
  } | null>(null);
  const [jobs, setJobs] = useState<Array<{id: number, title: string, company: string, addedAt: string}>>([]);
  const [selectedJobs, setSelectedJobs] = useState<number[]>([]);

  const formatDate = (dateString: string) => {
    try {
      if (!dateString) return '';
      
      // Handle both ISO format and our custom format
      const date = dateString.includes('T') 
        ? new Date(dateString)
        : new Date(dateString.replace(/(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2})/, '$1T$2'));
      
      return new Intl.DateTimeFormat('en-AU', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      }).format(date);
    } catch (err) {
      console.error('Error formatting date:', err);
      return dateString || 'Invalid date';
    }
  };

  const handleJobSelect = (jobId: number) => {
    setSelectedJobs(prev => 
      prev.includes(jobId) 
        ? prev.filter(id => id !== jobId)
        : [...prev, jobId]
    );
  };

  const handleDeleteCV = async () => {
    try {
      if (uploadedCV) {
        const response = await api.deleteCV(uploadedCV.id);
        if (response.success) {
          setUploadedCV(null);
          setMessage('CV deleted successfully');
        } else {
          setError('Failed to delete CV');
        }
      }
    } catch (err) {
      console.error('Error deleting CV:', err);
      setError(err instanceof Error ? err.message : 'Error deleting CV');
    }
  };

  const handleDeleteJob = async (jobId: number) => {
    try {
      const response = await api.deleteJobUrl(jobId);
      if (response.success) {
        setJobs(jobs.filter(job => job.id !== jobId));
        setMessage('Job deleted successfully');
      } else {
        setError('Failed to delete job');
      }
    } catch (err) {
      console.error('Error deleting job:', err);
      setError(err instanceof Error ? err.message : 'Error deleting job');
    }
  };

  // Load CV and jobs data
  useEffect(() => {
    const loadData = async () => {
      try {
        // Load CV data
        const cvResponse = await api.getUserCV();
        if (cvResponse.success && cvResponse.data) {
          setUploadedCV({
            id: cvResponse.data.id,
            name: cvResponse.data.filename,
            uploadTime: formatDate(cvResponse.data.created_at)
          });
        }

        // Load jobs data
        const jobsResponse = await api.getUserJobs();
        if (jobsResponse.success && jobsResponse.data) {
          setJobs(jobsResponse.data.map((job: any, index: number) => ({
            id: index,
            title: job.job_title || 'Untitled Position',
            company: job.company || 'Company Not Specified',
            addedAt: formatDate(job.created_at)
          })));
        }
      } catch (err) {
        console.error('Error loading data:', err);
      }
    };

    loadData();
  }, []);

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      const file = event.target.files[0];
      setSelectedFile(file);
      setError('');

      try {
        const response = await api.uploadCV(file);
        if (response.success && response.document) {
          // Set the CV data directly from the upload response
          setUploadedCV({
            id: response.document.id,
            name: response.document.filename,
            uploadTime: formatDate(response.document.created_at)
          });
          setMessage('CV uploaded successfully!');
        } else {
          setError('Failed to upload CV');
        }
      } catch (err) {
        console.error('Error uploading CV:', err);
        setError(err instanceof Error ? err.message : 'Error uploading CV');
      }
    }
  };

  const handleJobUrlSubmit = async () => {
    if (!jobUrl) {
      setError('Please enter a job URL');
      return;
    }

    if (!jobTitle) {
      setError('Please enter a job title');
      return;
    }

    if (!company) {
      setError('Please enter a company name');
      return;
    }

    try {
      const response = await api.addJobUrl({ 
        url: jobUrl,
        job_title: jobTitle,
        company_name: company
      });
      
      if (response.success && response.data) {
        setJobs([
          {
            id: response.data.id,
            title: response.data.job_title,
            company: response.data.company,
            addedAt: formatDate(response.data.created_at)
          },
          ...jobs
        ]);
        setJobUrl('');
        setJobTitle('');
        setCompany('');
        setMessage('Job URL added successfully!');
      } else {
        setError(response.error || 'Failed to add job URL');
      }
    } catch (err) {
      console.error('Error adding job URL:', err);
      setError(err instanceof Error ? err.message : 'Error adding job URL');
    }
  };

  if (!user) {
    navigate('/login');
    return null;
  }

  return (
    <>
      <NavBar />
      <Container maxWidth="lg">
        <Box sx={{ mt: 4 }}>
          {message && (
            <Box sx={{ mb: 2 }}>
              <Paper sx={{ p: 2, bgcolor: 'success.light', color: 'success.contrastText' }}>
                <Typography>{message}</Typography>
              </Paper>
            </Box>
          )}
          {error && (
            <Box sx={{ mb: 2 }}>
              <Paper sx={{ p: 2, bgcolor: 'error.light', color: 'error.contrastText' }}>
                <Typography>{error}</Typography>
              </Paper>
            </Box>
          )}
          <Grid container spacing={3}>
            {/* CV Card */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <UploadIcon sx={{ mr: 1 }} />
                    <Typography variant="h6">Your CV</Typography>
                  </Box>
                  <Divider sx={{ mb: 2 }} />
                  {uploadedCV ? (
                    <Box sx={{ mt: 2, p: 2, bgcolor: 'background.paper', borderRadius: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Box>
                          <Typography variant="subtitle1">{uploadedCV.name}</Typography>
                          <Typography variant="body2" color="text.secondary">
                            Uploaded: {uploadedCV.uploadTime}
                          </Typography>
                        </Box>
                        <IconButton 
                          onClick={handleDeleteCV}
                          color="error"
                          aria-label="delete CV"
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Box>
                    </Box>
                  ) : (
                    <Typography variant="body1" color="text.secondary">
                      No CV uploaded yet
                    </Typography>
                  )}
                </CardContent>
                <CardActions>
                  <input
                    accept=".doc,.docx,.pdf"
                    style={{ display: 'none' }}
                    id="cv-file"
                    type="file"
                    onChange={handleFileChange}
                  />
                  <label htmlFor="cv-file">
                    <Button component="span" variant="contained" fullWidth>
                      {uploadedCV ? 'Update CV' : 'Upload CV'}
                    </Button>
                  </label>
                </CardActions>
              </Card>
            </Grid>

            {/* Jobs Card */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <WorkIcon sx={{ mr: 1 }} />
                    <Typography variant="h6">Jobs to Apply For</Typography>
                  </Box>
                  <Divider sx={{ mb: 2 }} />
                  <Box component="form" sx={{ '& > :not(style)': { mb: 2 } }}>
                    <TextField
                      fullWidth
                      label="Job URL"
                      value={jobUrl}
                      onChange={(e) => setJobUrl(e.target.value)}
                      placeholder="https://example.com/job-posting"
                    />
                    <TextField
                      fullWidth
                      label="Job Title"
                      value={jobTitle}
                      onChange={(e) => setJobTitle(e.target.value)}
                      placeholder="Software Engineer"
                    />
                    <TextField
                      fullWidth
                      label="Company"
                      value={company}
                      onChange={(e) => setCompany(e.target.value)}
                      placeholder="Example Corp"
                    />
                    <Button
                      variant="contained"
                      fullWidth
                      onClick={handleJobUrlSubmit}
                      disabled={!jobUrl || !jobTitle || !company}
                    >
                      Add Job URL
                    </Button>
                  </Box>
                  <List>
                    {jobs.map((job, index) => (
                      <ListItem
                        key={index}
                        divider={index < jobs.length - 1}
                        secondaryAction={
                          <Box>
                            <IconButton
                              edge="end"
                              onClick={() => handleDeleteJob(job.id)}
                              color="error"
                              aria-label="delete job"
                              sx={{ mr: 1 }}
                            >
                              <DeleteIcon />
                            </IconButton>
                            <Checkbox
                              edge="end"
                              onChange={() => handleJobSelect(job.id)}
                              checked={selectedJobs.includes(job.id)}
                            />
                          </Box>
                        }
                      >
                        <ListItemText
                          primary={
                            <Typography variant="subtitle1">
                              {job.title} at {job.company}
                            </Typography>
                          }
                          secondary={`Added: ${job.addedAt}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>
      </Container>
    </>
  );
};

export default Dashboard;
