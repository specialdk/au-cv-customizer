import React, { useState } from 'react';
import axios from 'axios';
import {
  Box,
  Button,
  CircularProgress,
  Typography,
  Card,
  CardContent,
  Alert,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import { analyzeJob, testCVParse, testJobParse } from '../services/api';

interface AnalysisProps {
  cvId: number;
  jobUrl: string;
  onClose?: () => void;
}

interface AnalysisResult {
  matchScore: number;
  missingKeywords: string[];
  suggestedImprovements: string[];
  skillGaps: string[];
  optimizedSections: {
    summary?: string;
    experience?: string[];
    skills?: string[];
  };
}

const Analysis: React.FC<AnalysisProps> = ({ cvId, jobUrl, onClose }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);

  const handleAnalyze = async () => {
    if (!jobUrl || !cvId) {
      setError('Please select both a job URL and a CV');
      return;
    }

    // Check authentication
    const token = localStorage.getItem('token');
    if (!token) {
      setError('Please log in to analyze jobs');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // First test CV parsing
      console.log('Testing CV parsing...');
      const cvResult = await testCVParse(cvId);
      console.log('CV Parse Result:', cvResult);

      if (!cvResult.success) {
        setError('Failed to parse CV');
        setLoading(false);
        return;
      }

      // Then test job parsing
      console.log('Testing job parsing...');
      const jobResult = await testJobParse(jobUrl);
      console.log('Job Parse Result:', jobResult);

      if (!jobResult.success) {
        setError('Failed to parse job posting');
        setLoading(false);
        return;
      }

      // If both tests pass, proceed with analysis
      console.log('Both tests passed, proceeding with analysis...');
      const response = await analyzeJob(jobUrl, cvId);
      setResult(response.data);
    } catch (err) {
      console.error('Analysis error:', err);
      if (axios.isAxiosError(err) && err.response?.status === 401) {
        setError('Please log in to analyze jobs');
      } else {
        setError(err instanceof Error ? err.message : 'Failed to analyze');
      }
    } finally {
      setLoading(false);
    }
  };

  const renderMatchScore = () => {
    if (!result) return null;
    
    const score = result.matchScore;
    let color = '#f44336'; // red
    if (score >= 80) color = '#4caf50'; // green
    else if (score >= 60) color = '#ff9800'; // orange
    
    return (
      <Box sx={{ textAlign: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Match Score
        </Typography>
        <Box
          sx={{
            width: 120,
            height: 120,
            margin: '0 auto',
            borderRadius: '50%',
            border: '8px solid',
            borderColor: color,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Typography variant="h3" sx={{ color }}>
            {score}%
          </Typography>
        </Box>
      </Box>
    );
  };

  const renderSection = (title: string, items: string[]) => {
    if (!items || items.length === 0) return null;
    
    return (
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {title}
          </Typography>
          <List>
            {items.map((item, index) => (
              <React.Fragment key={index}>
                <ListItem>
                  <ListItemText primary={item} />
                </ListItem>
                {index < items.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        </CardContent>
      </Card>
    );
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        CV Analysis
      </Typography>

      {!result && (
        <Button
          variant="contained"
          onClick={handleAnalyze}
          disabled={loading}
          sx={{ mb: 3 }}
        >
          {loading ? (
            <>
              <CircularProgress size={24} sx={{ mr: 1 }} />
              Analyzing...
            </>
          ) : (
            'Analyze CV'
          )}
        </Button>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {result && (
        <Box>
          {renderMatchScore()}
          
          {renderSection('Missing Keywords', result.missingKeywords)}
          {renderSection('Suggested Improvements', result.suggestedImprovements)}
          {renderSection('Skill Gaps', result.skillGaps)}

          {result.optimizedSections && (
            <>
              {result.optimizedSections.summary && (
                <Card sx={{ mb: 2 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Optimized Summary
                    </Typography>
                    <Typography>
                      {result.optimizedSections.summary}
                    </Typography>
                  </CardContent>
                </Card>
              )}

              {renderSection('Optimized Experience Points', 
                result.optimizedSections.experience || [])}
              
              {renderSection('Optimized Skills', 
                result.optimizedSections.skills || [])}
            </>
          )}

          {onClose && (
            <Button 
              variant="outlined" 
              onClick={onClose}
              sx={{ mt: 2 }}
            >
              Close
            </Button>
          )}
        </Box>
      )}
    </Box>
  );
};

export default Analysis;
