import { useEffect, useState } from 'react';
import {
  DndContext,
  DragOverlay,
  closestCorners,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
  DragStartEvent,
} from '@dnd-kit/core';
import { sortableKeyboardCoordinates } from '@dnd-kit/sortable';
import { useBoardStore } from '@/stores/boardStore';
import { BoardColumn } from '@/components/Board/BoardColumn';
import { ApplicationCard } from '@/components/Cards/ApplicationCard';
import { Application, ApplicationStatus } from '@/types';
import { Plus, RefreshCw, Search, X } from 'lucide-react';
import { ApplicationModal } from '@/components/Modals/ApplicationModal';

const CARDS_PER_COLUMN = 15; // Show 15 cards per column, then "Load More"

export function BoardPage() {
  const { columns, applications, isLoading, fetchBoardData, moveApplication } = useBoardStore();
  const [activeId, setActiveId] = useState<string | null>(null);
  const [selectedApplication, setSelectedApplication] = useState<Application | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedColumns, setExpandedColumns] = useState<Set<string>>(new Set());

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  useEffect(() => {
    fetchBoardData();
  }, [fetchBoardData]);

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as string);
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveId(null);

    if (!over) return;

    const activeId = active.id as string;
    const overId = over.id as string;

    // Find which column the card is being dropped into
    const overColumn = columns.find((col) => col.id === overId);

    if (overColumn) {
      // Dropped on a column
      const applicationId = parseInt(activeId);
      await moveApplication(applicationId, overColumn.id);
    }
  };

  const getActiveApplication = () => {
    if (!activeId) return null;
    const id = parseInt(activeId);
    for (const status of Object.keys(applications) as ApplicationStatus[]) {
      const app = applications[status].find((a) => a.id === id);
      if (app) return app;
    }
    return null;
  };

  const filterApplications = (apps: Application[]) => {
    return apps.filter((app) => {
      const matchesSearch = !searchQuery || 
        app.company_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        app.position_title.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesSearch;
    });
  };

  const getFilteredApplications = () => {
    const filtered: Record<ApplicationStatus, Application[]> = {} as any;
    for (const status of Object.keys(applications) as ApplicationStatus[]) {
      filtered[status] = filterApplications(applications[status] || []);
    }
    return filtered;
  };

  const filteredApps = getFilteredApplications();
  const totalApps = Object.values(filteredApps).reduce((sum, apps) => sum + apps.length, 0);

  const toggleColumnExpanded = (columnId: string) => {
    const newExpanded = new Set(expandedColumns);
    if (newExpanded.has(columnId)) {
      newExpanded.delete(columnId);
    } else {
      newExpanded.add(columnId);
    }
    setExpandedColumns(newExpanded);
  };

  const getVisibleCards = (columnId: string, apps: Application[]) => {
    const isExpanded = expandedColumns.has(columnId);
    if (isExpanded) {
      return apps; // Show all
    }
    return apps.slice(0, CARDS_PER_COLUMN); // Show only first 15
  };

  const getHiddenCount = (columnId: string, apps: Application[]) => {
    const isExpanded = expandedColumns.has(columnId);
    if (isExpanded) {
      return 0;
    }
    return Math.max(0, apps.length - CARDS_PER_COLUMN);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="h-full space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Application Board</h1>
          <p className="text-gray-600 mt-1">Drag and drop to update application status</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => fetchBoardData()}
            className="flex items-center px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors font-medium"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </button>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="flex items-center px-4 py-2 text-white bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all shadow-sm font-medium"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Application
          </button>
        </div>
      </div>

      {/* Search and Filter Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          placeholder="Search by company or position..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-12 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
        />
        {searchQuery && (
          <button
            onClick={() => setSearchQuery('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Stats Bar */}
      {totalApps > 0 && (
        <div className="flex items-center space-x-4 text-sm text-gray-600 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <span className="font-semibold text-gray-900">{totalApps}</span>
          <span>application{totalApps !== 1 ? 's' : ''} found</span>
          {searchQuery && (
            <>
              <span className="text-gray-400">•</span>
              <span>Filtering by: <span className="font-medium text-gray-900">"{searchQuery}"</span></span>
            </>
          )}
        </div>
      )}

      {/* Board */}
      {isLoading ? (
        <div className="flex items-center justify-center h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <DndContext
          sensors={sensors}
          collisionDetection={closestCorners}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <div className="flex space-x-4 overflow-x-auto pb-4 -mx-4 px-4">
            {columns.map((column) => {
              const columnApps = filteredApps[column.id] || [];
              const visibleApps = getVisibleCards(column.id, columnApps);
              const hiddenCount = getHiddenCount(column.id, columnApps);

              return (
                <BoardColumn
                  key={column.id}
                  id={column.id}
                  title={column.title}
                  applications={columnApps}
                  visibleApplications={visibleApps}
                  hiddenCount={hiddenCount}
                  onCardClick={setSelectedApplication}
                  onLoadMore={() => toggleColumnExpanded(column.id)}
                />
              );
            })}
          </div>

          <DragOverlay>
            {activeId ? (
              <div className="opacity-90">
                {getActiveApplication() && (
                  <ApplicationCard
                    application={getActiveApplication()!}
                    onClick={() => {}}
                  />
                )}
              </div>
            ) : null}
          </DragOverlay>
        </DndContext>
      )}

      {/* Modals */}
      {selectedApplication && (
        <ApplicationModal
          application={selectedApplication}
          onClose={() => setSelectedApplication(null)}
        />
      )}

      {isCreateModalOpen && (
        <ApplicationModal
          onClose={() => {
            setIsCreateModalOpen(false);
            fetchBoardData();
          }}
        />
      )}
    </div>
  );
}
