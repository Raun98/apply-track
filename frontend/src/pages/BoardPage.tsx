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
import { OnboardingEmptyState } from '@/components/OnboardingEmptyState';
import { Application, ApplicationStatus } from '@/types';
import { Plus, RefreshCw, Search, X } from 'lucide-react';
import { ApplicationModal } from '@/components/Modals/ApplicationModal';

const CARDS_PER_COLUMN = 15; // Show 15 cards per column, then "Load More"

export function BoardPage() {
  const { columns, applications, isLoading, error, fetchBoardData, moveApplication } = useBoardStore();
  const [activeId, setActiveId] = useState<string | null>(null);
  const [selectedApplication, setSelectedApplication] = useState<Application | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedColumns, setExpandedColumns] = useState<Set<string>>(new Set());
  const [activeColumn, setActiveColumn] = useState(0);

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

    // `over` can be either a column (id = status string) or a card (id = number string).
    // Resolve to the target column in both cases.
    let targetColumnId = columns.find((col) => col.id === overId)?.id;

    if (!targetColumnId) {
      // Dropped on another card — find which column that card lives in
      const cardId = parseInt(overId);
      for (const col of columns) {
        const apps = applications[col.id as ApplicationStatus] || [];
        if (apps.some((a) => a.id === cardId)) {
          targetColumnId = col.id;
          break;
        }
      }
    }

    if (targetColumnId) {
      const applicationId = parseInt(activeId);
      await moveApplication(applicationId, targetColumnId as ApplicationStatus);
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

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <p className="text-red-600 font-medium">Failed to load board</p>
          <p className="text-sm text-gray-500 mt-1">{error}</p>
          <button
            onClick={() => fetchBoardData()}
            className="mt-4 px-4 py-2 text-sm text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Check if user has zero applications — show onboarding
  const hasApplications = totalApps > 0 || Object.values(applications).some(apps => apps.length > 0);
  if (!hasApplications && !searchQuery) {
    return (
      <>
        <OnboardingEmptyState onAddApplication={() => setIsCreateModalOpen(true)} />
        {isCreateModalOpen && (
          <ApplicationModal
            onClose={() => {
              setIsCreateModalOpen(false);
              fetchBoardData();
            }}
          />
        )}
      </>
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
              <span className="text-gray-400">&bull;</span>
              <span>Filtering by: <span className="font-medium text-gray-900">"{searchQuery}"</span></span>
            </>
          )}
        </div>
      )}

      {/* Mobile Tab Bar */}
      <div className="md:hidden flex overflow-x-auto border-b border-gray-200 mb-4 -mx-4 px-4">
        {columns.map((col, i) => {
          const colApps = filteredApps[col.id] || [];
          return (
            <button
              key={col.id}
              onClick={() => setActiveColumn(i)}
              className={`px-4 py-2 text-sm font-medium whitespace-nowrap border-b-2 transition ${
                activeColumn === i
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-400'
              }`}
            >
              {col.title} ({colApps.length})
            </button>
          );
        })}
      </div>

      {/* Board */}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        {/* Desktop: horizontal flex with all columns */}
        <div className="hidden md:flex space-x-4 overflow-x-auto pb-4 -mx-4 px-4">
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

        {/* Mobile: single column at a time */}
        <div className="md:hidden">
          {columns.length > 0 && (() => {
            const column = columns[activeColumn];
            if (!column) return null;
            const columnApps = filteredApps[column.id] || [];
            const visibleApps = getVisibleCards(column.id, columnApps);
            const hiddenCount = getHiddenCount(column.id, columnApps);

            return (
              <div className="space-y-2">
                {visibleApps.map((application) => (
                  <MobileCard
                    key={application.id}
                    application={application}
                    columns={columns}
                    currentStatus={column.id}
                    onCardClick={setSelectedApplication}
                    onMove={async (appId, toCol) => {
                      await moveApplication(appId, toCol);
                    }}
                  />
                ))}
                {hiddenCount > 0 && (
                  <button
                    onClick={() => toggleColumnExpanded(column.id)}
                    className="w-full py-2 px-3 text-xs font-semibold text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    Load more ({hiddenCount} hidden)
                  </button>
                )}
                {columnApps.length === 0 && (
                  <div className="text-center py-8 text-gray-400 text-sm">
                    No applications in this column
                  </div>
                )}
              </div>
            );
          })()}
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

/** Mobile card with a "Move to..." dropdown instead of drag-and-drop */
function MobileCard({
  application,
  columns,
  currentStatus,
  onCardClick,
  onMove,
}: {
  application: Application;
  columns: { id: ApplicationStatus; title: string }[];
  currentStatus: ApplicationStatus;
  onCardClick: (app: Application) => void;
  onMove: (appId: number, toCol: ApplicationStatus) => Promise<void>;
}) {
  const [showMoveMenu, setShowMoveMenu] = useState(false);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <div onClick={() => onCardClick(application)} className="cursor-pointer">
        <div className="flex items-start justify-between mb-1">
          <h4 className="font-semibold text-gray-900 truncate">{application.company_name}</h4>
        </div>
        <p className="text-sm text-gray-600 line-clamp-2">{application.position_title}</p>
        {application.location && (
          <p className="text-xs text-gray-400 mt-1 truncate">{application.location}</p>
        )}
      </div>

      {/* Move to dropdown */}
      <div className="mt-3 pt-2 border-t border-gray-100 relative">
        <button
          onClick={(e) => {
            e.stopPropagation();
            setShowMoveMenu(!showMoveMenu);
          }}
          className="text-xs text-blue-600 font-medium hover:text-blue-800"
        >
          Move to...
        </button>
        {showMoveMenu && (
          <div className="absolute bottom-full left-0 mb-1 bg-white border border-gray-200 rounded-lg shadow-lg z-10 py-1 min-w-[140px]">
            {columns
              .filter((col) => col.id !== currentStatus)
              .map((col) => (
                <button
                  key={col.id}
                  onClick={async (e) => {
                    e.stopPropagation();
                    setShowMoveMenu(false);
                    await onMove(application.id, col.id);
                  }}
                  className="block w-full text-left px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
                >
                  {col.title}
                </button>
              ))}
          </div>
        )}
      </div>
    </div>
  );
}
