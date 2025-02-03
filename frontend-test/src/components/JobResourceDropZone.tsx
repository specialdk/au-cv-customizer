import React, { useState, useRef, DragEvent, ChangeEvent } from 'react';
import { 
  Box, 
  Typography, 
  Button, 
  Dialog, 
  DialogActions, 
  DialogContent, 
  DialogContentText, 
  DialogTitle,
  Tabs,
  Tab
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import LinkIcon from '@mui/icons-material/Link';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';

interface JobResourceDropZoneProps {
  onURLSubmit: (url: string) => void;
  onDocumentSubmit: (file: File) => void;
}

const JobResourceDropZone: React.FC<JobResourceDropZoneProps> = ({ 
  onURLSubmit, 
  onDocumentSubmit 
}) => {
  const [dragOver, setDragOver] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [urlInput, setUrlInput] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleFileDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    
    const files = e.dataTransfer?.files;
    if (files && files.length > 0) {
      setSelectedFile(files[0]);
    }
  };

  const handleFileInput = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      setSelectedFile(files[0]);
    }
  };

  const handleSubmitURL = () => {
    if (urlInput.trim()) {
      onURLSubmit(urlInput.trim());
      setUrlInput('');
    }
  };

  const handleSubmitDocument = () => {
    if (selectedFile) {
      onDocumentSubmit(selectedFile);
      setSelectedFile(null);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  return (
    <Box>
      <Tabs 
        value={activeTab} 
        onChange={handleTabChange} 
        centered
        sx={{ mb: 2 }}
      >
        <Tab icon={<LinkIcon />} label="Job URL" />
        <Tab icon={<InsertDriveFileIcon />} label="Job Document" />
      </Tabs>

      {activeTab === 0 && (
        <Box 
          sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            width: '100%' 
          }}
        >
          <input
            type="text"
            placeholder="Paste Job URL here"
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            style={{ 
              flexGrow: 1, 
              padding: '10px', 
              marginRight: '10px',
              border: '1px solid #ccc',
              borderRadius: '4px'
            }}
          />
          <Button 
            variant="contained" 
            color="primary"
            onClick={handleSubmitURL}
            disabled={!urlInput.trim()}
          >
            Add URL
          </Button>
        </Box>
      )}

      {activeTab === 1 && (
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
            {selectedFile 
              ? `Selected: ${selectedFile.name}` 
              : 'Drag and drop a job document or click to select'}
          </Typography>
          {selectedFile && (
            <Button 
              variant="contained" 
              color="primary" 
              sx={{ mt: 2 }}
              onClick={handleSubmitDocument}
            >
              Upload Document
            </Button>
          )}
        </Box>
      )}
    </Box>
  );
};

export default JobResourceDropZone;
