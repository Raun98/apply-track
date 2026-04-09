import { useDroppable } from '@dnd-kit/core';
import {
  SortableContext,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { Application, ApplicationStatus } from '@/types';
import { ApplicationCard } from '@/components/Cards/ApplicationCard';
import { cn } from '@/lib/utils';

interface BoardColumnProps {
  id: ApplicationStatus;
  title: string;
  applications: Application[];
  visibleApplications: Application[];
  hiddenCount: number;
  onCardClick: (application: Application) => void;
  onLoadMore: () => void;
}

const columnColors: Record<ApplicationStatus, string> = {
  applied: 'bg-gray-100 border-gray-200',
  screening: 'bg-blue-50 border-blue-200',
  interview: 'bg-yellow-50 border-yellow-200',
  offer: 'bg-green-50 border-green-200',
  rejected: 'bg-red-50 border-red-200',
  accepted: 'bg-purple-50 border-purple-200',
};

const columnHeaderColors: Record<ApplicationStatus, string> = {
  applied: 'text-gray-700',
  screening: 'text-blue-700',
  interview: 'text-yellow-700',
  offer: 'text-green-700',
  rejected: 'text-red-700',
  accepted: 'text-purple-700',
};

export function BoardColumn({ 
  id, 
  title, 
  applications,
  visibleApplications,
  hiddenCount,
  onCardClick,
  onLoadMore 
}: BoardColumnProps) {
  const { isOver, setNodeRef } = useDroppable({
    id,
  });

  return (
    <div
      ref={setNodeRef}
      className={cn(
        'flex flex-col w-80 min-w-80 max-w-80 rounded-xl border-2 transition-colors shadow-sm',
        columnColors[id],
        isOver && 'ring-2 ring-blue-400 border-blue-400'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-inherit">
        <h3 className={cn('font-bold text-sm', columnHeaderColors[id])}>
          {title}
        </h3>
        <span className="px-2.5 py-1 text-xs font-bold bg-white rounded-full shadow-sm">
          {applications.length}
        </span>
      </div>

      {/* Cards */}
      <div className="flex-1 p-3 space-y-3 overflow-y-auto max-h-[70vh]">
        <SortableContext
          items={visibleApplications.map((app) => app.id.toString())}
          strategy={verticalListSortingStrategy}
        >
          {visibleApplications.map((application) => (
            <ApplicationCard
              key={application.id}
              application={application}
              onClick={() => onCardClick(application)}
            />
          ))}
        </SortableContext>

        {/* Load More Button */}
        {hiddenCount > 0 && (
          <button
            onClick={onLoadMore}
            className="w-full mt-2 py-2 px-3 text-xs font-semibold text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Load {Math.min(10, hiddenCount)} more ({hiddenCount} hidden)
          </button>
        )}
      </div>
    </div>
  );
}
