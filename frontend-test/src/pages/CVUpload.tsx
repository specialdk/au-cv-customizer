import React, { useState, useEffect, useCallback } from 'react';
import { uploadCV } from '../services/api';
import { 
  Button, 
  Typography, 
  Box, 
  Alert,
  CircularProgress
} from '@mui/material';

interface CVUploadProps {
  onUploadSuccess?: () => void;
  onClose?: () => void;
}

const CVUpload: React.FC<CVUploadProps> = ({ onUploadSuccess, onClose }) => {
  const [file, setFile] = useState<File | null>(null);
  const [uploadState, setUploadState] = useState<'idle' | 'uploading' | 'processing' | 'completed' | 'failed'>('idle');
  const [uploadStatus, setUploadStatus] = useState<{
    success: boolean;
    message: string;
  } | null>(null);
  
  // Ref to store the cancel function
  const cancelUploadRef = React.useRef<(() => void) | null>(null);

  // Cleanup function
  const cleanup = useCallback(() => {
    if (cancelUploadRef.current) {
      console.log('Cleaning up - cancelling polling');
      cancelUploadRef.current();
      cancelUploadRef.current = null;
    }
    setFile(null);
    setUploadState('idle');
    setUploadStatus(null);
  }, []);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setFile(event.target.files[0]);
      setUploadState('idle');
      setUploadStatus(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setUploadStatus({
        success: false,
        message: 'Please select a file first',
      });
      return;
    }

    try {
      // Clean up any previous upload
      cleanup();
      
      setUploadState('uploading');
      setUploadStatus(null);
      
      const response = await uploadCV(file, (status) => {
        console.log('Upload status update:', status);
        switch (status) {
          case 'uploading':
            setUploadState('uploading');
            break;
          case 'processing':
            setUploadState('processing');
            break;
          case 'completed':
            setUploadState('completed');
            setUploadStatus({
              success: true,
              message: 'CV uploaded and processed successfully!',
            });
            // Clear file selection
            setFile(null);
            // Show success message and then trigger success callback
            setTimeout(() => {
              cleanup();
              if (onUploadSuccess) {
                onUploadSuccess();
              }
              if (onClose) {
                onClose();
              }
            }, 1500);
            break;
          case 'failed':
            setUploadState('failed');
            setUploadStatus({
              success: false,
              message: 'Failed to process CV. Please try again.',
            });
            break;
        }
      });
      
      if (response) {
        // Store the cancel function
        cancelUploadRef.current = response.cancelPolling;
      }
    } catch (error) {
      console.error('Upload error:', error);
      setUploadState('failed');
      setUploadStatus({
        success: false,
        message: error instanceof Error ? error.message : 'Failed to upload CV',
      });
    }
  };

  // Cleanup effect when component unmounts
  useEffect(() => {
    return cleanup;
  }, [cleanup]);

  return (
    <Box sx={{ maxWidth: 600, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Upload CV
      </Typography>
      
      <input
        accept=".doc,.docx,.pdf"
        style={{ display: 'none' }}
        id="cv-upload"
        type="file"
        onChange={handleFileChange}
        disabled={uploadState === 'uploading' || uploadState === 'processing'}
      />
      
      <Box sx={{ mb: 3 }}>
        <label htmlFor="cv-upload">
          <Button
            variant="contained"
            component="span"
            disabled={uploadState === 'uploading' || uploadState === 'processing'}
          >
            Select File
          </Button>
        </label>
        {file && (
          <Typography sx={{ ml: 2, display: 'inline' }}>
            {file.name}
          </Typography>
        )}
      </Box>

      {uploadState !== 'idle' && (
        <Box sx={{ mb: 3, display: 'flex', alignItems: 'center' }}>
          {(uploadState === 'uploading' || uploadState === 'processing') && (
            <CircularProgress size={24} sx={{ mr: 2 }} />
          )}
          <Typography>
            {uploadState === 'uploading' && 'Uploading CV...'}
            {uploadState === 'processing' && 'Processing CV...'}
            {uploadState === 'completed' && 'Upload Complete!'}
            {uploadState === 'failed' && 'Upload Failed'}
          </Typography>
        </Box>
      )}

      {uploadStatus && (
        <Alert 
          severity={uploadStatus.success ? 'success' : 'error'} 
          sx={{ mb: 3 }}
        >
          {uploadStatus.message}
        </Alert>
      )}

      <Button
        variant="contained"
        onClick={handleUpload}
        disabled={!file || uploadState === 'uploading' || uploadState === 'processing'}
        sx={{ mr: 2 }}
      >
        Upload
      </Button>
    </Box>
  );
};

export default CVUpload;
