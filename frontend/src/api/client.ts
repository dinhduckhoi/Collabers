import { TokenPair, User, Profile, Project, Application, Collaboration, Conversation, Message, Notification } from '../types';

const API_BASE = '/api';

function getTokens(): { access: string | null; refresh: string | null } {
  return {
    access: localStorage.getItem('access_token'),
    refresh: localStorage.getItem('refresh_token'),
  };
}

function setTokens(tokens: TokenPair): void {
  localStorage.setItem('access_token', tokens.access_token);
  localStorage.setItem('refresh_token', tokens.refresh_token);
}

function clearTokens(): void {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

async function refreshAccessToken(): Promise<boolean> {
  const { refresh } = getTokens();
  if (!refresh) return false;

  try {
    const response = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refresh }),
    });

    if (response.ok) {
      const tokens: TokenPair = await response.json();
      setTokens(tokens);
      return true;
    }
    clearTokens();
    return false;
  } catch {
    clearTokens();
    return false;
  }
}

async function fetchWithAuth<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  const { access } = getTokens();
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (access) {
    headers['Authorization'] = `Bearer ${access}`;
  }

  let response = await fetch(url, { ...options, headers });

  if (response.status === 401 && access) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      const { access: newAccess } = getTokens();
      headers['Authorization'] = `Bearer ${newAccess}`;
      response = await fetch(url, { ...options, headers });
    }
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
    throw new Error(error.detail || 'An error occurred');
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const authApi = {
  register: async (email: string, password: string): Promise<TokenPair> => {
    const response = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!response.ok) {
      const error = await response.json();
      // Handle both string detail and array of validation errors
      if (Array.isArray(error.detail)) {
        const messages = error.detail.map((e: { msg: string }) => e.msg).join(', ');
        throw new Error(messages);
      }
      throw new Error(error.detail || 'Registration failed');
    }
    const tokens: TokenPair = await response.json();
    setTokens(tokens);
    return tokens;
  },

  login: async (email: string, password: string): Promise<TokenPair> => {
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!response.ok) {
      const error = await response.json();
      // Handle both string detail and array of validation errors
      if (Array.isArray(error.detail)) {
        const messages = error.detail.map((e: { msg: string }) => e.msg).join(', ');
        throw new Error(messages);
      }
      throw new Error(error.detail || 'Login failed');
    }
    const tokens: TokenPair = await response.json();
    setTokens(tokens);
    return tokens;
  },

  logout: (): void => {
    clearTokens();
  },

  getMe: (): Promise<User> => fetchWithAuth(`${API_BASE}/auth/me`),

  sendVerificationEmail: (): Promise<{ message: string; dev_otp?: string; dev_link_token?: string }> =>
    fetchWithAuth(`${API_BASE}/auth/resend-verification`, { method: 'POST' }),

  verifyEmail: async (otp: string): Promise<{ message: string }> => {
    return fetchWithAuth(`${API_BASE}/auth/verify-otp`, {
      method: 'POST',
      body: JSON.stringify({ otp }),
    });
  },

  requestPasswordReset: async (email: string): Promise<{ message: string; dev_otp?: string; dev_link_token?: string }> => {
    const response = await fetch(`${API_BASE}/auth/request-password-reset`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to request password reset');
    }
    return response.json();
  },

  resetPasswordWithOtp: async (email: string, otp: string, newPassword: string): Promise<{ message: string }> => {
    const response = await fetch(`${API_BASE}/auth/reset-password-otp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, otp, new_password: newPassword }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Password reset failed');
    }
    return response.json();
  },

  resetPasswordWithLink: async (token: string, newPassword: string): Promise<{ message: string }> => {
    const response = await fetch(`${API_BASE}/auth/reset-password-link`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, new_password: newPassword }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Password reset failed');
    }
    return response.json();
  },

  isAuthenticated: (): boolean => !!getTokens().access,
};

export const profileApi = {
  getMyProfile: (): Promise<Profile> => fetchWithAuth(`${API_BASE}/profile/me`),

  createProfile: (data: Partial<Profile>): Promise<Profile> =>
    fetchWithAuth(`${API_BASE}/profile/me`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateProfile: (data: Partial<Profile>): Promise<Profile> =>
    fetchWithAuth(`${API_BASE}/profile/me`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  uploadAvatar: async (file: File): Promise<Profile> => {
    const { access } = getTokens();
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE}/profile/me/avatar`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${access}`,
      },
      body: formData,
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(error.detail || 'Upload failed');
    }
    
    return response.json();
  },

  getUserProfile: (userId: number): Promise<Profile> =>
    fetchWithAuth(`${API_BASE}/profile/${userId}`),
};

export interface ProjectFilters {
  skip?: number;
  limit?: number;
  category?: string;
  tech_stack?: string;
  role?: string;
  commitment?: string;
  duration?: string;
  search?: string;
}

export const projectsApi = {
  getProjects: (filters: ProjectFilters = {}): Promise<Project[]> => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== '') {
        params.append(key, String(value));
      }
    });
    const query = params.toString() ? `?${params.toString()}` : '';
    return fetchWithAuth(`${API_BASE}/projects${query}`);
  },

  getProject: (id: number): Promise<Project> => fetchWithAuth(`${API_BASE}/projects/${id}`),

  createProject: (data: Partial<Project>): Promise<Project> =>
    fetchWithAuth(`${API_BASE}/projects`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateProject: (id: number, data: Partial<Project>): Promise<Project> =>
    fetchWithAuth(`${API_BASE}/projects/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  deleteProject: (id: number): Promise<void> =>
    fetchWithAuth(`${API_BASE}/projects/${id}`, { method: 'DELETE' }),

  getMyProjects: (): Promise<Project[]> => fetchWithAuth(`${API_BASE}/projects/my`),
};

export const applicationsApi = {
  createApplication: (data: { project_id: number; cover_letter?: string; proposed_role?: string }): Promise<Application> =>
    fetchWithAuth(`${API_BASE}/applications`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getMyApplications: (): Promise<Application[]> => fetchWithAuth(`${API_BASE}/applications/my`),

  getProjectApplications: (projectId: number): Promise<Application[]> =>
    fetchWithAuth(`${API_BASE}/applications/project/${projectId}`),

  getApplication: (id: number): Promise<Application> => fetchWithAuth(`${API_BASE}/applications/${id}`),

  updateApplication: (id: number, data: { status?: string }): Promise<Application> =>
    fetchWithAuth(`${API_BASE}/applications/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
};

export const collaborationsApi = {
  getMyCollaborations: (): Promise<Collaboration[]> =>
    fetchWithAuth(`${API_BASE}/collaborations/my`),

  getProjectCollaborations: (projectId: number): Promise<Collaboration[]> =>
    fetchWithAuth(`${API_BASE}/collaborations/project/${projectId}`),

  leaveCollaboration: (collaborationId: number): Promise<{ message: string }> =>
    fetchWithAuth(`${API_BASE}/collaborations/${collaborationId}/leave`, { method: 'POST' }),

  removeMember: (collaborationId: number, userId: number): Promise<{ message: string }> =>
    fetchWithAuth(`${API_BASE}/collaborations/${collaborationId}/members/${userId}`, {
      method: 'DELETE',
    }),
};

export const conversationsApi = {
  getConversations: (): Promise<Conversation[]> => fetchWithAuth(`${API_BASE}/conversations`),

  getConversation: (id: number, skip = 0, limit = 50): Promise<Conversation> =>
    fetchWithAuth(`${API_BASE}/conversations/${id}?skip=${skip}&limit=${limit}`),

  sendMessage: (conversationId: number, content: string): Promise<Message> =>
    fetchWithAuth(`${API_BASE}/conversations/${conversationId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    }),

  markAsRead: (conversationId: number): Promise<{ message: string }> =>
    fetchWithAuth(`${API_BASE}/conversations/${conversationId}/read`, { method: 'POST' }),
};

export const notificationsApi = {
  getNotifications: (unreadOnly = false): Promise<Notification[]> =>
    fetchWithAuth(`${API_BASE}/notifications?unread_only=${unreadOnly}`),

  getUnreadCount: (): Promise<{ unread_count: number }> =>
    fetchWithAuth(`${API_BASE}/notifications/count`),

  markAsRead: (id: number): Promise<Notification> =>
    fetchWithAuth(`${API_BASE}/notifications/${id}/read`, { method: 'POST' }),

  markAllAsRead: (): Promise<{ message: string }> =>
    fetchWithAuth(`${API_BASE}/notifications/read-all`, { method: 'POST' }),
};

export const reportsApi = {
  create: (data: {
    reported_user_id?: number;
    reported_project_id?: number;
    reason: string;
    details?: string;
  }): Promise<{ id: number }> =>
    fetchWithAuth(`${API_BASE}/reports`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
};
