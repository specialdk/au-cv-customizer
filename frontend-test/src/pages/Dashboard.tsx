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
} from '@mui/material';
import { UploadFile as UploadIcon, Work as WorkIcon } from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import * as api from '../services/api';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [jobUrl, setJobUrl] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [uploadedCV, setUploadedCV] = useState<{name: string, uploadTime: string} | null>(null);
  const [jobs, setJobs] = useState<Array<{title: string, company: string, addedAt: string}>>([]);

  // Load CV and jobs data
  useEffect(() => {
    const loadData = async () => {
      try {
        // Load CV data
        const cvResponse = await api.getUserCV();
        if (cvResponse.success) {
          setUploadedCV({
            name: cvResponse.data.filename,
            uploadTime: new Date(cvResponse.data.uploadTime).toLocaleString()
          });
        }

        // Load jobs data
        const jobsResponse = await api.getUserJobs();
        if (jobsResponse.success) {
          setJobs(jobsResponse.data.map((job: any) => ({
            title: job.title || 'Untitled Position',
            company: job.company || 'Company Not Specified',
            addedAt: new Date(job.created_at).toLocaleString()
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
        const formData = new FormData();
        formData.append('file', file);
        const response = await api.uploadCV(formData);

        if (response.success) {
          setUploadedCV({
            name: file.name,
            uploadTime: new Date().toLocaleString()
          });
          setMessage('CV uploaded successfully!');
        } else {
          setError('Failed to upload CV');
        }
      } catch (err) {
        console.error('Error uploading CV:', err);
        setError('Error uploading CV');
      }
    }
  };

  const handleJobUrlSubmit = async () => {
    if (!jobUrl) {
      setError('Please enter a job URL');
      return;
    }

    try {
      const response = await api.addJobUrl({ url: jobUrl });
      
      if (response.success) {
        setJobs([
          {
            title: response.data.title || 'Untitled Position',
            company: response.data.company || 'Company Not Specified',
            addedAt: new Date().toLocaleString()
          },
          ...jobs
        ]);
        setJobUrl('');
        setMessage('Job URL added successfully!');
      } else {
        setError('Failed to add job URL');
      }
    } catch (err) {
      console.error('Error adding job URL:', err);
      setError('Error adding job URL');
    }
  };

  if (!user) {
    navigate('/login');
    return null;
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4 }}>
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
                  <>
                    <Typography variant="body1" gutterBottom>
                      Current CV: {uploadedCV.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Uploaded: {uploadedCV.uploadTime}
                    </Typography>
                  </>
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
                <Box sx={{ mb: 2 }}>
                  <TextField
                    fullWidth
                    label="Job Posting URL"
                    variant="outlined"
                    value={jobUrl}
                    onChange={(e) => setJobUrl(e.target.value)}
                    placeholder="Enter job posting URL"
                    size="small"
                  />
                </Box>
                <List>
                  {jobs.map((job, index) => (
                    <ListItem key={index} divider={index < jobs.length - 1}>
                      <ListItemText
                        primary={job.title}
                        secondary={
                          <>
                            {job.company}
                            <br />
                            Added: {job.addedAt}
                          </>
                        }
                      />
                    </ListItem>
                  ))}
                  {jobs.length === 0 && (
                    <Typography variant="body2" color="text.secondary" align="center">
                      No jobs added yet
                    </Typography>
                  )}
                </List>
              </CardContent>
              <CardActions>
                <Button 
                  variant="contained" 
                  fullWidth 
                  onClick={handleJobUrlSubmit}
                  disabled={!jobUrl}
                >
                  Add Job
                </Button>
              </CardActions>
            </Card>
          </Grid>

          {/* Messages */}
          {(error || message) && (
            <Grid item xs={12}>
              {error && (
                <Typography color="error" align="center">
                  {error}
                </Typography>
              )}
              {message && (
                <Typography color="primary" align="center">
                  {message}
                </Typography>
              )}
            </Grid>
          )}
        </Grid>
      </Box>
    </Container>
  );
};

export default Dashboard;
