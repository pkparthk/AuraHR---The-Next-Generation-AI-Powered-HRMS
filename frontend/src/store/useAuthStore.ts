import { create } from "zustand";
import { persist } from "zustand/middleware";
import { authApi } from "@/lib/api";

export type UserRole = "admin" | "manager" | "recruiter" | "employee";

export interface User {
  id: string;
  email: string;
  role: UserRole;
  employee_id?: string;
  created_at?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
  setUser: (user: User, token: string) => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authApi.login({ email, password });
          const user: User = {
            id: response.user.id,
            email: response.user.email,
            role: response.user.role as UserRole,
            employee_id: response.user.employee_id,
            created_at: response.user.created_at,
          };

          set({
            user,
            token: response.access_token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || "Login failed";
          set({
            error: errorMessage,
            isLoading: false,
            isAuthenticated: false,
            user: null,
            token: null,
          });
          throw new Error(errorMessage);
        }
      },

      register: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const user = await authApi.register({ email, password });
          // After registration, automatically log in
          await get().login(email, password);
        } catch (error: any) {
          const errorMessage =
            error.response?.data?.detail || "Registration failed";
          set({
            error: errorMessage,
            isLoading: false,
          });
          throw new Error(errorMessage);
        }
      },

      logout: () => {
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          error: null,
        });
      },

      setUser: (user: User, token: string) => {
        set({ user, token, isAuthenticated: true, error: null });
      },

      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: "auth-storage",
    }
  )
);
