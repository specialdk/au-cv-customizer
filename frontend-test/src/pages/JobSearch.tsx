import React, { useState } from 'react';
import { Button, Typography, Alert, Box, Container } from '@mui/material';
import JobURLManager from '../components/JobURLManager';
import { useNavigate } from 'react-router-dom';

interface JobSearchProps {
  onUploadSuccess?: () => void;
}

const JobSearch: React.FC<JobSearchProps> = ({ onUploadSuccess }) => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<{
    success: boolean;
    message: string;
  } | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setFile(event.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setUploadStatus({
        success: false,
        message: 'Please select a job description file',
      });
      return;
    }

    try {
      // Placeholder for job description upload/processing logic
      const jobDetails = await processJobDescription(file);
      
      setUploadStatus({
        success: true,
        message: 'Job details processed successfully!',
      });

      if (onUploadSuccess) {
        onUploadSuccess();
      }

      setFile(null);
    } catch (error) {
      const errorMessage = error instanceof Error 
        ? error.message 
        : 'Failed to process job description. Please try again.';
      
      setUploadStatus({
        success: false,
        message: errorMessage,
      });
    }
  };

  const handleURLAdded = () => {
    // Navigate back to the landing page after successful URL addition
    navigate('/');
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ mt: 4 }}>
        <Typography variant="h4" gutterBottom>
          Job Search Management
        </Typography>

        <Box sx={{ mb: 4 }}>
          <Typography variant="h6" gutterBottom>
            Upload Job Description
          </Typography>
          
          <Button
            variant="contained"
            component="label"
            fullWidth
            sx={{ mt: 'auto' }}
          >
            Choose Job Description
            <input
              type="file"
              hidden
              accept=".txt,.pdf,.doc,.docx"
              onChange={handleFileChange}
            />
          </Button>

          {file && (
            <>
              <Typography variant="body2" sx={{ mt: 1, mb: 1, textAlign: 'center' }}>
                Selected: {file.name}
              </Typography>
              <Button 
                variant="contained" 
                color="primary" 
                onClick={handleUpload}
                fullWidth
                sx={{ mt: 1 }}
              >
                Process Job Description
              </Button>
            </>
          )}

          {uploadStatus && (
            <Alert 
              severity={uploadStatus.success ? 'success' : 'error'}
              sx={{ mt: 2, width: '100%' }}
            >
              {uploadStatus.message}
            </Alert>
          )}
        </Box>

        <JobURLManager onURLAdded={handleURLAdded} />
      </Box>
    </Container>
  );
};

// This is a placeholder function - implement actual job description processing logic
const processJobDescription = async (file: File) => {
  // Implement your job description processing logic here
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        success: true,
        message: 'Job description processed successfully'
      });
    }, 1000);
  });
};

export default JobSearch;
