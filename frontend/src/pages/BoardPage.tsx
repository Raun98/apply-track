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
import { Plus, RefreshCw } from 'lucide-react';
import { ApplicationModal } from '@/components/Modals/ApplicationModal';

export function BoardPage() {
  const { columns, applications, isLoading, fetchBoardData, moveApplication } = useBoardStore();
  const [activeId, setActiveId] = useState<string | null>(null);
  const [selectedApplication, setSelectedApplication] = useState<Application | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Application Board</h1>
          <p className="text-gray-600">Drag and drop to update application status</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => fetchBoardData()}
            className="flex items-center px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </button>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="flex items-center px-4 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Application
          </button>
        </div>
      </div>

      {/* Board */}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <div className="flex space-x-4 overflow-x-auto pb-4">
          {columns.map((column) => (
            <BoardColumn
              key={column.id}
              id={column.id}
              title={column.title}
              applications={applications[column.id] || []}
              onCardClick={setSelectedApplication}
            />
          ))}
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
