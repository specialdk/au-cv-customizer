import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Button,
  Box,
  TextField,
  Grid,
  FormControlLabel,
  Checkbox,
} from '@mui/material';
import { useAuth } from '../contexts/AuthContext';
import * as api from '../services/api';
import Analysis from '../components/Analysis';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [jobUrl, setJobUrl] = useState('');
  const [applyChanges, setApplyChanges] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [cvId, setCvId] = useState<number | null>(null);
  const [showAnalysis, setShowAnalysis] = useState(false);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0]);
      setError('');
    }
  };

  const handleJobUrlChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setJobUrl(event.target.value);
    setError('');
  };

  const handleAnalyse = async () => {
    if (!selectedFile) {
      setError('Please select a CV file');
      return;
    }

    if (!jobUrl) {
      setError('Please enter a job posting URL');
      return;
    }

    try {
      setMessage('Uploading CV...');
      const cvResponse = await api.uploadCV(selectedFile);
      
      if (cvResponse.success) {
        // For now, we'll use a temporary ID
        setCvId(1); // We'll need to get the actual ID from the backend later
        setShowAnalysis(true);
      } else {
        setError(cvResponse.message || 'Failed to upload CV');
      }
      
    } catch (err) {
      console.error('Error:', err);
      setError('An error occurred while processing your request');
      setMessage('');
    }
  };

  if (!user) {
    navigate('/login');
    return null;
  }

  return (
    <Container maxWidth="md">
      <Box sx={{ mt: 4 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom align="center">
            CV Customizer
          </Typography>
          
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Box sx={{ mb: 2 }}>
                <input
                  accept=".doc,.docx"
                  style={{ display: 'none' }}
                  id="cv-file"
                  type="file"
                  onChange={handleFileChange}
                />
                <label htmlFor="cv-file">
                  <Button variant="contained" component="span" fullWidth>
                    Select CV
                  </Button>
                </label>
                {selectedFile && (
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    Selected file: {selectedFile.name}
                  </Typography>
                )}
              </Box>
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Job Posting URL"
                variant="outlined"
                value={jobUrl}
                onChange={handleJobUrlChange}
                placeholder="Enter the URL of the job posting"
              />
            </Grid>

            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={applyChanges}
                    onChange={(e) => setApplyChanges(e.target.checked)}
                  />
                }
                label="Apply changes to CV"
              />
            </Grid>

            <Grid item xs={12}>
              <Button
                variant="contained"
                color="primary"
                fullWidth
                onClick={handleAnalyse}
                disabled={!selectedFile || !jobUrl}
              >
                Analyse
              </Button>
            </Grid>

            {error && (
              <Grid item xs={12}>
                <Typography color="error" align="center">
                  {error}
                </Typography>
              </Grid>
            )}

            {message && (
              <Grid item xs={12}>
                <Typography color="primary" align="center">
                  {message}
                </Typography>
              </Grid>
            )}
          </Grid>
        </Paper>
      </Box>

      {showAnalysis && cvId && (
        <Box sx={{ mt: 4 }}>
          <Paper elevation={3} sx={{ p: 4 }}>
            <Analysis 
              cvId={cvId}
              jobUrl={jobUrl}
              onClose={() => setShowAnalysis(false)}
            />
          </Paper>
        </Box>
      )}
    </Container>
  );
};

export default Dashboard;
