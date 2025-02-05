import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  CircularProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  Checkbox,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import * as api from '../services/api';
import MatchAnalysis from './MatchAnalysis';
import { JobURL, MatchPoint } from '../types';
import { useNavigate } from 'react-router-dom';

interface JobURLManagerProps {
  onJobCountChange?: (count: number) => void;
}

const JobURLManager: React.FC<JobURLManagerProps> = ({ onJobCountChange }) => {
  const [jobUrls, setJobUrls] = useState<JobURL[]>([]);
  const [newUrl, setNewUrl] = useState('');
  const [jobTitle, setJobTitle] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [selectedUrl, setSelectedUrl] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<{ match_points: MatchPoint[], overall_score: number } | null>(null);
  const [appliedJobs, setAppliedJobs] = useState<Set<number>>(new Set());
  const navigate = useNavigate();

  useEffect(() => {
    fetchJobUrls();
  }, []);

  const fetchJobUrls = async () => {
    try {
      setLoading(true);
      const urls = await api.getJobURLs();
      setJobUrls(urls);
      if (onJobCountChange) {
        onJobCountChange(urls.length);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch job URLs');
    } finally {
      setLoading(false);
    }
  };

  const handleAddUrl = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUrl || !jobTitle || !companyName) {
      setError('Please fill in all fields');
      return;
    }

    try {
      setLoading(true);
      await api.addJobUrl({
        url: newUrl,
        job_title: jobTitle,
        company: companyName
      });
      setSuccess('Job URL added successfully');
      setNewUrl('');
      setJobTitle('');
      setCompanyName('');
      await fetchJobUrls();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add job URL');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUrl = async (id: number) => {
    try {
      setLoading(true);
      await api.deleteJobURL(id);
      setSuccess('Job URL deleted successfully');
      await fetchJobUrls();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete job URL');
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeUrl = async (url: string) => {
    setSelectedUrl(url);
    try {
      setLoading(true);
      const result = await api.analyzeJobMatch({}, url);
      setAnalysisResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze job match');
    } finally {
      setLoading(false);
    }
  };

  const handleApplyForJob = async (jobUrl: JobURL) => {
    try {
      setLoading(true);
      await api.createApplication(jobUrl.job_title, jobUrl.company, jobUrl.url);
      setSuccess('Application created successfully');
      setAppliedJobs(prev => new Set([...prev, jobUrl.id]));
      navigate('/applications');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create application');
    } finally {
      setLoading(false);
    }
  };

  const handleCloseAnalysis = () => {
    setSelectedUrl(null);
    setAnalysisResult(null);
  };

  const handleAnalysisProceed = async (selectedMatches: MatchPoint[]) => {
    try {
      await api.storeMatchSelections(selectedMatches);
      handleCloseAnalysis();
      setSuccess('Match analysis saved successfully');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save match analysis');
    }
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Job URLs
      </Typography>

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" onClose={() => setSuccess(null)} sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      <Box component="form" onSubmit={handleAddUrl} sx={{ mb: 3 }}>
        <TextField
          fullWidth
          label="Job URL"
          value={newUrl}
          onChange={(e) => setNewUrl(e.target.value)}
          margin="normal"
          required
        />
        <TextField
          fullWidth
          label="Job Title"
          value={jobTitle}
          onChange={(e) => setJobTitle(e.target.value)}
          margin="normal"
          required
        />
        <TextField
          fullWidth
          label="Company Name"
          value={companyName}
          onChange={(e) => setCompanyName(e.target.value)}
          margin="normal"
          required
        />
        <Button
          type="submit"
          variant="contained"
          disabled={loading}
          sx={{ mt: 2 }}
        >
          Add Job URL
        </Button>
      </Box>

      <List>
        {jobUrls.map((jobUrl) => (
          <ListItem key={jobUrl.id}>
            <ListItemText
              primary={jobUrl.job_title}
              secondary={
                <>
                  {jobUrl.company}
                  <br />
                  {jobUrl.url}
                </>
              }
            />
            <ListItemSecondaryAction>
              {jobUrls.length > 0 && !appliedJobs.has(jobUrl.id) && (
                <Button
                  onClick={() => handleApplyForJob(jobUrl)}
                  disabled={loading}
                  variant="contained"
                  color="primary"
                  sx={{ mr: 1 }}
                >
                  Apply
                </Button>
              )}
              <Button
                onClick={() => handleAnalyzeUrl(jobUrl.url)}
                disabled={loading}
                sx={{ mr: 1 }}
              >
                Analyze
              </Button>
              <IconButton
                edge="end"
                onClick={() => handleDeleteUrl(jobUrl.id)}
                disabled={loading}
              >
                <DeleteIcon />
              </IconButton>
            </ListItemSecondaryAction>
          </ListItem>
        ))}
      </List>

      {loading && (
        <Box display="flex" justifyContent="center" p={3}>
          <CircularProgress />
        </Box>
      )}

      <Dialog
        open={!!selectedUrl && !!analysisResult}
        onClose={handleCloseAnalysis}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Job Match Analysis</DialogTitle>
        <DialogContent sx={{ p: 3 }}>
          {selectedUrl && analysisResult && (
            <MatchAnalysis
              jobUrl={selectedUrl}
              onClose={handleCloseAnalysis}
              matches={analysisResult.match_points}
              overallScore={analysisResult.overall_score}
              onProceed={handleAnalysisProceed}
            />
          )}
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default JobURLManager;
