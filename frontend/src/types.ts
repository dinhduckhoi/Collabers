export interface User {
  id: number;
  email: string;
  email_verified: boolean;
  created_at: string;
  last_active: string;
  account_status: string;
  profile?: Profile;
}

export interface Profile {
  id: number;
  user_id: number;
  full_name: string;
  headline: string;
  avatar_url?: string;
  bio?: string;
  skills: string[];
  roles: string[];
  availability: string;
  github_url?: string;
  linkedin_url?: string;
  portfolio_url?: string;
  interests: string[];
  profile_completeness: number;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: number;
  creator_id: number;
  title: string;
  description: string;
  detailed_description?: string;
  category: string;
  tech_stack: string[];
  roles_needed: string[];
  commitment_hours: string;
  duration: string;
  team_size: number;
  status: string;
  visibility: string;
  views_count: number;
  created_at: string;
  updated_at: string;
  creator?: User;
  application_count?: number;
}

export interface Application {
  id: number;
  project_id: number;
  applicant_id: number;
  cover_letter?: string;
  proposed_role?: string;
  status: string;
  created_at: string;
  updated_at: string;
  applicant?: User;
  project?: Project;
}

export interface Collaboration {
  id: number;
  project_id: number;
  user_id: number;
  role: string;
  status: string;
  joined_at: string;
  left_at?: string;
  project?: Project;
  user?: User;
}

export interface Message {
  id: number;
  conversation_id: number;
  sender_id: number;
  content: string;
  created_at: string;
  read_by?: number[];
  sender?: User;
  sender_profile?: Profile;
}

export interface Conversation {
  id: number;
  project_id?: number;
  type: string;
  created_at: string;
  updated_at: string;
  last_message?: Message;
  messages?: Message[];
  project?: Project;
  unread_count?: number;
}

export interface Notification {
  id: number;
  user_id: number;
  type: string;
  reference_type: string;
  reference_id: number;
  title: string;
  message?: string;
  project_id?: number;
  is_read: boolean;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface ApiError {
  detail: string;
}
