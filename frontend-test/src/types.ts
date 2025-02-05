export interface JobURL {
  id: number;
  url: string;
  job_title: string;
  company: string;
  created_at: string;
}

export interface MatchPoint {
  category: string;
  description: string;
  confidence: number;
  evidence?: string;
}

export interface MatchAnalysisProps {
  jobUrl: string;
  onClose: () => void;
  matches: MatchPoint[];
  overallScore: number;
  onProceed?: (selectedMatches: MatchPoint[]) => Promise<void>;
}
