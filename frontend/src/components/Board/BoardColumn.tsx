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
  onCardClick: (application: Application) => void;
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

export function BoardColumn({ id, title, applications, onCardClick }: BoardColumnProps) {
  const { isOver, setNodeRef } = useDroppable({
    id,
  });

  return (
    <div
      ref={setNodeRef}
      className={cn(
        'flex flex-col w-80 min-w-80 max-w-80 rounded-lg border-2 transition-colors',
        columnColors[id],
        isOver && 'ring-2 ring-blue-400 border-blue-400'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-inherit">
        <h3 className={cn('font-semibold', columnHeaderColors[id])}>
          {title}
        </h3>
        <span className="px-2 py-1 text-xs font-medium bg-white rounded-full shadow-sm">
          {applications.length}
        </span>
      </div>

      {/* Cards */}
      <div className="flex-1 p-3 space-y-3 min-h-[200px]">
        <SortableContext
          items={applications.map((app) => app.id.toString())}
          strategy={verticalListSortingStrategy}
        >
          {applications.map((application) => (
            <ApplicationCard
              key={application.id}
              application={application}
              onClick={() => onCardClick(application)}
            />
          ))}
        </SortableContext>
      </div>
    </div>
  );
}
