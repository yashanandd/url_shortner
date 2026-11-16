const API_BASE = "http://localhost:8000/api/v1";

export const getAccessToken = () => localStorage.getItem("linkflow_access_token");
export const getRefreshToken = () => localStorage.getItem("linkflow_refresh_token");

export const setAuthTokens = (access, refresh) => {
  if (access) localStorage.setItem("linkflow_access_token", access);
  if (refresh) localStorage.setItem("linkflow_refresh_token", refresh);
};

export const clearAuthTokens = () => {
  localStorage.removeItem("linkflow_access_token");
  localStorage.removeItem("linkflow_refresh_token");
  localStorage.removeItem("linkflow_user");
};

export const getCurrentUser = () => {
  const user = localStorage.getItem("linkflow_user");
  return user ? JSON.parse(user) : null;
};

export const setCurrentUser = (user) => {
  localStorage.setItem("linkflow_user", JSON.stringify(user));
};

async function apiRequest(endpoint, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  const token = getAccessToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  let response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  // Handle Token Refresh on 401 Unauthorized
  if (response.status === 401 && getRefreshToken() && !options._retry) {
    options._retry = true;
    try {
      const refreshRes = await fetch(`${API_BASE}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: getRefreshToken() }),
      });

      if (refreshRes.ok) {
        const tokenData = await refreshRes.json();
        setAuthTokens(tokenData.access_token, tokenData.refresh_token);
        headers["Authorization"] = `Bearer ${tokenData.access_token}`;
        response = await fetch(`${API_BASE}${endpoint}`, {
          ...options,
          headers,
        });
      } else {
        clearAuthTokens();
        window.dispatchEvent(new Event("auth_change"));
      }
    } catch {
      clearAuthTokens();
      window.dispatchEvent(new Event("auth_change"));
    }
  }

  if (!response.ok) {
    let errorDetail = "Request failed";
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorJson.error || errorDetail;
    } catch {
      // response wasn't JSON
    }
    throw new Error(errorDetail);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export const api = {
  auth: {
    register: async (email, password, name) => {
      const res = await apiRequest("/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password, name }),
      });
      return res;
    },
    login: async (email, password) => {
      const tokens = await apiRequest("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setAuthTokens(tokens.access_token, tokens.refresh_token);
      const user = await api.auth.me();
      setCurrentUser(user);
      window.dispatchEvent(new Event("auth_change"));
      return { tokens, user };
    },
    logout: async () => {
      const refresh = getRefreshToken();
      if (refresh) {
        try {
          await apiRequest("/auth/logout", {
            method: "POST",
            body: JSON.stringify({ refresh_token: refresh }),
          });
        } catch {
          // ignore logout network failure
        }
      }
      clearAuthTokens();
      window.dispatchEvent(new Event("auth_change"));
    },
    me: async () => {
      return apiRequest("/auth/me");
    },
  },
  urls: {
    create: async (original_url, custom_alias = null, expires_at = null) => {
      return apiRequest("/urls/", {
        method: "POST",
        body: JSON.stringify({
          original_url,
          custom_alias: custom_alias || null,
          expires_at: expires_at || null,
        }),
      });
    },
    list: async (skip = 0, limit = 50) => {
      return apiRequest(`/urls/?skip=${skip}&limit=${limit}`);
    },
    get: async (urlId) => {
      return apiRequest(`/urls/${urlId}`);
    },
    update: async (urlId, updateData) => {
      return apiRequest(`/urls/${urlId}`, {
        method: "PATCH",
        body: JSON.stringify(updateData),
      });
    },
    delete: async (urlId) => {
      return apiRequest(`/urls/${urlId}`, {
        method: "DELETE",
      });
    },
  },
  analytics: {
    get: async (shortCode, days = 30) => {
      return apiRequest(`/analytics/${shortCode}?days=${days}`);
    },
  },
};
