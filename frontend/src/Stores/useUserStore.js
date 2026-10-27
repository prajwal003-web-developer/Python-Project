
import { create } from "zustand";

const useUserStore = create((set) => ({
  // Initial state
  isLoggedIn: false,
  user: null,

  // Set login status directly
  setIsLoggedIn: (isLoggedIn) => set({ isLoggedIn }),

  // Set user data directly
  setUser: (user) => set({ user }),

  // Update both after successful login
  setAuth: (user) =>
    set({
      user,
      isLoggedIn: true,
    }),

  // Clear authentication data after logout
  clearAuth: () =>
    set({
      user: null,
      isLoggedIn: false,
    }),
}));

export default useUserStore;
