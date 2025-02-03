import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Chip,
  Alert,
  Snackbar,
  Stack,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import { getJobURLs, addJobUrl, deleteJobURL } from '../services/api';

interface JobURL {
  id: number;
  url: string;
  job_title: string;
  company_name: string;
  created_at: string;
}

interface JobURLManagerProps {
  onURLAdded?: () => void;
  onJobCountChange?: (count: number) => void;
}

const JobURLManager: React.FC<JobURLManagerProps> = ({ onURLAdded, onJobCountChange }) => {
  const [jobUrls, setJobUrls] = useState<JobURL[]>([]);
  const [newUrl, setNewUrl] = useState('');
  const [jobTitle, setJobTitle] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const fetchJobUrls = async () => {
    try {
      setLoading(true);
      const urls = await getJobURLs();
      setJobUrls(urls);
      if (onJobCountChange) {
        onJobCountChange(urls.length);
      }
    } catch (err) {
      setError('Failed to fetch job URLs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobUrls();
  }, []);

  const handleAddUrl = async () => {
    if (!newUrl || !jobTitle || !companyName) {
      setError('Please fill in all fields');
      return;
    }

    try {
      setLoading(true);
      await addJobUrl({
        url: newUrl,
        job_title: jobTitle,
        company_name: companyName
      });
      setNewUrl('');
      setJobTitle('');
      setCompanyName('');
      setSuccess('Job URL added successfully');
      if (onURLAdded) {
        onURLAdded();
      }
      await fetchJobUrls();
    } catch (err) {
      setError('Failed to add job URL');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUrl = async (id: number) => {
    try {
      setLoading(true);
      await deleteJobURL(id);
      setSuccess('Job URL deleted successfully');
      await fetchJobUrls();
    } catch (err) {
      setError('Failed to delete job URL');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <TextField
          label="Job URL"
          value={newUrl}
          onChange={(e) => setNewUrl(e.target.value)}
          fullWidth
          size="small"
        />
        <TextField
          label="Job Title"
          value={jobTitle}
          onChange={(e) => setJobTitle(e.target.value)}
          fullWidth
          size="small"
        />
        <TextField
          label="Company Name"
          value={companyName}
          onChange={(e) => setCompanyName(e.target.value)}
          fullWidth
          size="small"
        />
        <Button
          variant="contained"
          onClick={handleAddUrl}
          disabled={loading}
        >
          {loading ? <CircularProgress size={24} /> : 'Add URL'}
        </Button>
      </Box>

      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
      >
        <Alert onClose={() => setError(null)} severity="error">
          {error}
        </Alert>
      </Snackbar>

      <Snackbar
        open={!!success}
        autoHideDuration={6000}
        onClose={() => setSuccess(null)}
      >
        <Alert onClose={() => setSuccess(null)} severity="success">
          {success}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default JobURLManager;
