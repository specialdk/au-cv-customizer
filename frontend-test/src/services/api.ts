import axios, { AxiosError } from 'axios';

const API_BASE_URL = 'http://localhost:5000';

interface ErrorResponse {
  error: string;
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Add a request interceptor
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add a response interceptor
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ErrorResponse>) => {
    console.error('API Error:', error);
    if (error.response?.data?.error) {
      throw new Error(error.response.data.error);
    }
    throw error;
  }
);

export interface JobURL {
  id: number;
  url: string;
  job_title: string;
  company: string;
  created_at: string;
}

export interface JobDetails {
  url: string;
  job_title: string;
  company: string;
}

export const getJobURLs = async (): Promise<JobURL[]> => {
  const response = await api.get('/api/jobs/urls');
  return response.data;
};

export const addJobUrl = async (details: JobDetails): Promise<JobURL> => {
  const response = await api.post('/api/jobs/urls', details);
  return response.data.data; // Backend returns { success: true, data: JobURL }
};

export const deleteJobURL = async (urlId: number): Promise<void> => {
  await api.delete(`/api/jobs/urls/${urlId}`);
};

export const analyzeJobMatch = async (cvData: any, jobUrl: string) => {
  const response = await api.post('/api/analyze/job-match', {
    cv_data: cvData,
    job_url: jobUrl,
  });
  return response.data;
};

export const getAuthToken = () => localStorage.getItem('access_token');

export const setAuthToken = (token: string) => {
  localStorage.setItem('access_token', token);
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
};

export const clearAuthToken = () => {
  localStorage.removeItem('access_token');
  delete api.defaults.headers.common['Authorization'];
};

export const login = async (email: string, password: string) => {
  try {
    console.log('API login request:', { email, password });
    const response = await api.post('/api/login', { email, password });
    console.log('API login response:', response.data);

    if (response.data.access_token) {
      setAuthToken(response.data.access_token);
      // Store user info in localStorage
      if (response.data.user) {
        console.log('Storing user in localStorage:', response.data.user);
        localStorage.setItem('user', JSON.stringify(response.data.user));
      }
    }

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error('API Error:', error);
      if (error.response?.data?.error) {
        console.error('Login Error:', error.response.data);
        throw new Error(error.response.data.error);
      }
    }
    throw error;
  }
};

export const register = async (email: string, password: string, name: string) => {
  try {
    console.log('API register request:', { email, password, name });
    const response = await api.post('/api/register', { 
      email, 
      password, 
      name 
    });
    console.log('API register response:', response.data);

    if (response.data.access_token) {
      setAuthToken(response.data.access_token);
      if (response.data.user) {
        localStorage.setItem('user', JSON.stringify(response.data.user));
      }
    }

    return response.data;
  } catch (error) {
    console.error('API Error:', error);
    if (axios.isAxiosError(error) && error.response?.data?.error) {
      throw new Error(error.response.data.error);
    }
    throw error;
  }
};

export const getDocumentStatus = async (documentId: number) => {
  try {
    const response = await api.get(`/api/documents/${documentId}/status`);
    return response.data;
  } catch (error) {
    console.error('Get document status error:', error);
    throw error;
  }
};

interface UploadResponse {
  success: boolean;
  message: string;
  document?: {
    id: number;
    filename: string;
    document_type: string;
    created_at: string;
    updated_at: string | null;
  };
  cancelPolling: () => void;
}

export const uploadCV = async (file: File, onProgress?: (status: string) => void): Promise<UploadResponse> => {
  // Create an AbortController to handle cancellation
  const abortController = new AbortController();
  let isPollingCancelled = false;

  try {
    onProgress?.('uploading');
    console.log('API uploadCV request:', JSON.stringify({ file: file.name }, null, 2));
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', 'cv'); // Set document type to cv
  
    const response = await api.post('/api/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      signal: abortController.signal
    });
    
    console.log('API uploadCV response:', JSON.stringify(response.data, null, 2));
    
    // Start polling for status if document was created
    if (response.data.document?.id) {
      onProgress?.('processing');
      
      // Poll for status every 2 seconds
      const pollStatus = async () => {
        try {
          const statusResponse = await api.get(`/api/documents/${response.data.document.id}/status`);
          console.log('Status response:', statusResponse.data);
          
          if (statusResponse.data.status === 'completed') {
            isPollingCancelled = true; // Stop polling when complete
            return;
          }
          
          if (!isPollingCancelled) {
            setTimeout(pollStatus, 1000);
          }
        } catch (error) {
          if (!isPollingCancelled) {
            console.error('Error polling status:', error);
            onProgress?.('failed');
            throw error;
          }
        }
      };
      
      // Start polling
      pollStatus().catch(error => {
        if (!isPollingCancelled) {
          console.error('Polling failed:', error);
          onProgress?.('failed');
        }
      });
    }
    
    // Return both the response data and a function to cancel polling
    return {
      success: response.data.success,
      message: response.data.message,
      document: response.data.document,
      cancelPolling: () => {
        console.log('Cancelling polling');
        isPollingCancelled = true;
        abortController.abort();
      }
    };
  } catch (error: unknown) {
    if (error instanceof Error && error.name === 'AbortError') {
      console.log('Request aborted');
      return {
        success: false,
        message: 'Upload cancelled',
        cancelPolling: () => {
          isPollingCancelled = true;
          abortController.abort();
        }
      };
    }
    onProgress?.('failed');
    if (axios.isAxiosError(error)) {
      // Log detailed error information
      console.error('Upload CV Error Details:', {
        response: error.response?.data,
        status: error.response?.status,
        message: error.message,
        config: error.config
      });
      
      // Throw a more informative error
      throw new Error(
        error.response?.data?.message || 
        error.message || 
        'Failed to upload CV'
      );
    } else {
      console.error('Unexpected Upload CV Error:', error);
      throw error;
    }
  }
};

export const createApplication = async (
  jobTitle: string, 
  company: string, 
  jobUrl: string
) => {
  try {
    console.log('API createApplication request:', JSON.stringify({ jobTitle, company, jobUrl }, null, 2));
    const response = await api.post('/api/applications', { jobTitle, company, jobUrl });
    console.log('API createApplication response:', JSON.stringify(response.data, null, 2));
    return response.data;
  } catch (error: unknown) {
    if (axios.isAxiosError(error)) {
      console.error('Create Application Error:', error.response ? JSON.stringify(error.response.data, null, 2) : error.message);
    } else {
      console.error('Unexpected Create Application Error:', error);
    }
    throw error;
  }
};

export const getApplications = async () => {
  try {
    console.log('API getApplications request');
    const response = await api.get('/api/applications');
    console.log('API getApplications response:', JSON.stringify(response.data, null, 2));
    return response.data;
  } catch (error: unknown) {
    if (axios.isAxiosError(error)) {
      console.error('Get Applications Error:', error.response ? JSON.stringify(error.response.data, null, 2) : error.message);
    } else {
      console.error('Unexpected Get Applications Error:', error);
    }
    throw error;
  }
};

export const getCVs = async () => {
  try {
    console.log('API getCVs request');
    const response = await api.get('/api/documents');
    console.log('API getCVs response:', JSON.stringify(response.data, null, 2));
    return response.data;
  } catch (error: unknown) {
    if (axios.isAxiosError(error)) {
      console.error('Get CVs Error:', error.response ? JSON.stringify(error.response.data, null, 2) : error.message);
    } else {
      console.error('Unexpected Get CVs Error:', error);
    }
    throw error;
  }
};

interface UserProfile {
  id: number;
  email: string;
  name: string;
}

export const getUserProfile = async (): Promise<UserProfile> => {
  try {
    const response = await api.get<UserProfile>('/api/profile');
    return response.data;
  } catch (error) {
    console.error('Get Profile Error:', error);
    throw error;
  }
};

export const updateProfile = async (data: { name: string; email: string }): Promise<UserProfile> => {
  try {
    const response = await api.put<UserProfile>('/api/user', data);
    return response.data;
  } catch (error) {
    console.error('Update Profile Error:', error);
    throw error;
  }
};

export const deleteCV = async (documentId: number) => {
  try {
    console.log('API deleteCV request:', JSON.stringify({ documentId }, null, 2));
    const response = await api.delete(`/api/documents/${documentId}`);
    console.log('API deleteCV response:', JSON.stringify(response.data, null, 2));
    return {
      success: true,
      data: response.data
    };
  } catch (error) {
    console.error('Error deleting CV:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to delete CV'
    };
  }
};

export interface JobResource {
  id: number;
  type: 'url' | 'document';
  content: string;
  created_at: string;
}

export const createJobDocument = async (resource: { 
  type: 'url' | 'document', 
  content: string | File | JobDetails 
}): Promise<JobResource> => {
  try {
    console.log('API createJobDocument request:', JSON.stringify(resource, null, 2));
    const formData = new FormData();
    
    if (resource.type === 'url') {
      const content = typeof resource.content === 'string' 
        ? resource.content 
        : JSON.stringify(resource.content);
      
      const response = await api.post('/api/jobs/urls', {
        url: typeof resource.content === 'string' 
          ? resource.content 
          : (resource.content as JobDetails).url,
        job_title: typeof resource.content === 'string'
          ? new URL(resource.content).hostname
          : (resource.content as JobDetails).job_title,
        company_name: typeof resource.content === 'string'
          ? ''
          : (resource.content as JobDetails).company
      });
      console.log('API createJobDocument response:', JSON.stringify(response.data, null, 2));
      return response.data.data; // Backend returns { success: true, data: JobResource }
    } else {
      // Handle document upload
      formData.append('file', resource.content as File);
      formData.append('type', resource.type);
      
      const response = await api.post('/api/job-resources/document', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      console.log('API createJobDocument response:', JSON.stringify(response.data, null, 2));
      return response.data;
    }
  } catch (error) {
    console.error('Create Job Resource Error:', error);
    throw error;
  }
};

export const getJobResources = async (): Promise<JobResource[]> => {
  try {
    console.log('API getJobResources request');
    const response = await api.get('/api/job-resources');
    console.log('API getJobResources response:', JSON.stringify(response.data, null, 2));
    return response.data;
  } catch (error: unknown) {
    if (axios.isAxiosError(error)) {
      console.error('Get Job Resources Error:', error.response ? JSON.stringify(error.response.data, null, 2) : error.message);
    } else {
      console.error('Unexpected Get Job Resources Error:', error);
    }
    throw error;
  }
};

export const deleteJobResource = async (resourceId: number): Promise<void> => {
  try {
    console.log('API deleteJobResource request:', JSON.stringify({ resourceId }, null, 2));
    await api.delete(`/api/job-resources/${resourceId}`);
  } catch (error: unknown) {
    if (axios.isAxiosError(error)) {
      console.error('Delete Job Resource Error:', error.response ? JSON.stringify(error.response.data, null, 2) : error.message);
    } else {
      console.error('Unexpected Delete Job Resource Error:', error);
    }
    throw error;
  }
};

export const analyzeJob = async (jobUrl: string, cvId: number) => {
  try {
    console.log('API analyzeJob request:', JSON.stringify({ job_url: jobUrl, cv_id: cvId }, null, 2));
    const response = await api.post('/api/analyze-job', { 
      job_url: jobUrl, 
      cv_id: cvId 
    });
    console.log('API analyzeJob response:', JSON.stringify(response.data, null, 2));
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error('Analyze Job Error:', error.response ? JSON.stringify(error.response.data, null, 2) : error.message);
    } else {
      console.error('Unexpected Analyze Job Error:', error);
    }
    throw error;
  }
};

export const testCVParse = async (cvId: number) => {
  try {
    console.log('API testCVParse request for CV:', cvId);
    const token = getAuthToken();
    if (!token) {
      throw new Error('No authentication token found');
    }
    
    const response = await api.get(`/api/test-cv/${cvId}`);
    console.log('API testCVParse response:', JSON.stringify(response.data, null, 2));
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error('Test CV Parse Error:', error.response ? JSON.stringify(error.response.data, null, 2) : error.message);
    } else {
      console.error('Unexpected Test CV Parse Error:', error);
    }
    throw error;
  }
};

export const testJobParse = async (jobUrl: string) => {
  try {
    console.log('API testJobParse request:', JSON.stringify({ job_url: jobUrl }, null, 2));
    const token = getAuthToken();
    if (!token) {
      throw new Error('No authentication token found');
    }
    
    const response = await api.post('/api/test-job', { job_url: jobUrl });
    console.log('API testJobParse response:', JSON.stringify(response.data, null, 2));
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error('Test Job Parse Error:', error.response ? JSON.stringify(error.response.data, null, 2) : error.message);
    } else {
      console.error('Unexpected Test Job Parse Error:', error);
    }
    throw error;
  }
};

export const getUserCV = async () => {
  try {
    const response = await api.get('/api/documents/cv');
    return {
      success: true,
      data: response.data
    };
  } catch (error) {
    console.error('Error getting user CV:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to get CV'
    };
  }
};

export const getUserJobs = async () => {
  try {
    const response = await api.get('/api/jobs');
    return {
      success: true,
      data: response.data
    };
  } catch (error) {
    console.error('Error getting user jobs:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to get jobs'
    };
  }
};

// CV-Job Matching endpoints
export const getCurrentCV = async () => {
  return api.get('/api/cv/current');
};

export const storeMatchSelections = async (selectedMatches: any[]) => {
  return api.post('/api/analyze/store-selections', { selected_matches: selectedMatches });
};

// Initialize auth header if token exists
const token = getAuthToken();
if (token) {
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
}

export default api;
