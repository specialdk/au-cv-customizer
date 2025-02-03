import React, { useState, useRef, DragEvent, ChangeEvent } from 'react';
import { 
  Box, 
  Typography, 
  Button, 
  Dialog, 
  DialogActions, 
  DialogContent, 
  DialogContentText, 
  DialogTitle 
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';

interface URLDropZoneProps {
  onURLExtracted: (url: string) => void;
}

const URLDropZone: React.FC<URLDropZoneProps> = ({ onURLExtracted }) => {
  const [dragOver, setDragOver] = useState(false);
  const [extractedURL, setExtractedURL] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const extractURLFromFile = async (file: File) => {
    try {
      const text = await file.text();
      // Basic URL extraction regex
      const urlRegex = /(https?:\/\/[^\s]+)/g;
      const matches = text.match(urlRegex);
      
      if (matches && matches.length > 0) {
        setExtractedURL(matches[0]);
      } else {
        // If no URL found, try to use filename
        const potentialURL = file.name.replace(/\s+/g, '');
        if (potentialURL.startsWith('http://') || potentialURL.startsWith('https://')) {
          setExtractedURL(potentialURL);
        }
      }
    } catch (error) {
      console.error('Error reading file:', error);
    }
  };

  const handleFileDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    
    const files = e.dataTransfer?.files;
    if (files && files.length > 0) {
      extractURLFromFile(files[0]);
    }
  };

  const handleFileInput = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      extractURLFromFile(files[0]);
    }
  };

  const handleConfirmURL = () => {
    if (extractedURL) {
      onURLExtracted(extractedURL);
      setExtractedURL(null);
    }
  };

  const handleCancelURL = () => {
    setExtractedURL(null);
  };

  return (
    <>
      <Box
        sx={{
          border: '2px dashed',
          borderColor: dragOver ? 'primary.main' : 'grey.400',
          borderRadius: 2,
          p: 2,
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all 0.3s ease',
          '&:hover': {
            borderColor: 'primary.main',
            backgroundColor: 'rgba(0,0,0,0.04)'
          }
        }}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleFileDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          type="file"
          ref={fileInputRef}
          style={{ display: 'none' }}
          onChange={handleFileInput}
        />
        <CloudUploadIcon 
          sx={{ 
            fontSize: 50, 
            color: dragOver ? 'primary.main' : 'grey.500' 
          }} 
        />
        <Typography variant="body1" color="textSecondary">
          Drag and drop a file or click to select
        </Typography>
        <Typography variant="caption" color="textSecondary">
          We'll try to extract a job URL from the file
        </Typography>
      </Box>

      <Dialog
        open={!!extractedURL}
        onClose={handleCancelURL}
      >
        <DialogTitle>URL Detected</DialogTitle>
        <DialogContent>
          <DialogContentText>
            We found the following URL in the file:
          </DialogContentText>
          <Typography variant="h6" color="primary">
            {extractedURL}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancelURL} color="secondary">
            Cancel
          </Button>
          <Button onClick={handleConfirmURL} color="primary" autoFocus>
            Load this URL
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default URLDropZone;
