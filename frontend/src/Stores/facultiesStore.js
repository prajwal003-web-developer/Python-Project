import { create } from "zustand";

const useFacultyStore = create((set) => ({
  data: [],
  setData: (data) => set({ data }),

  isFetched: false,
  setIsFetched: (isFetched) => set({ isFetched }),

  loading: false,
  setLoading: (loading) => set({ loading }),

  error: null,
  setError: (error) => set({ error }),
}));

export default useFacultyStore;