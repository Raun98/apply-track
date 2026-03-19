import { create } from 'zustand';
import { Application, ApplicationStatus, BoardColumn, BoardData, StatsOverview } from '@/types';
import { boardApi } from '@/services/api';

interface BoardState {
  columns: BoardColumn[];
  applications: Record<ApplicationStatus, Application[]>;
  stats: StatsOverview | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchBoardData: () => Promise<void>;
  fetchStats: () => Promise<void>;
  moveApplication: (applicationId: number, toColumn: ApplicationStatus) => Promise<void>;
  updateApplicationInBoard: (application: Application) => void;
  addApplicationToBoard: (application: Application) => void;
}

export const useBoardStore = create<BoardState>((set, get) => ({
  columns: [],
  applications: {
    applied: [],
    screening: [],
    interview: [],
    offer: [],
    rejected: [],
    accepted: [],
  },
  stats: null,
  isLoading: false,
  error: null,

  fetchBoardData: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await boardApi.getApplications();
      const data: BoardData = response.data;
      set({
        columns: data.columns,
        applications: data.data,
        isLoading: false,
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch board data',
        isLoading: false,
      });
    }
  },

  fetchStats: async () => {
    try {
      const response = await boardApi.getStats();
      set({ stats: response.data });
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  },

  moveApplication: async (applicationId: number, toColumn: ApplicationStatus) => {
    try {
      await boardApi.moveCard(applicationId, toColumn);
      await get().fetchBoardData();
    } catch (error) {
      console.error('Failed to move application:', error);
      throw error;
    }
  },

  updateApplicationInBoard: (application: Application) => {
    const { applications } = get();
    const newApplications = { ...applications };

    // Remove from old status
    Object.keys(newApplications).forEach((status) => {
      newApplications[status as ApplicationStatus] = newApplications[status as ApplicationStatus].filter(
        (app) => app.id !== application.id
      );
    });

    // Add to new status
    newApplications[application.status].push(application);

    set({ applications: newApplications });
  },

  addApplicationToBoard: (application: Application) => {
    const { applications } = get();
    const newApplications = { ...applications };
    newApplications[application.status].push(application);
    set({ applications: newApplications });
  },
}));
