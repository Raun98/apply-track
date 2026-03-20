import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Application, JobSource } from '@/types';
import { Building2, MapPin, Calendar, Linkedin, Mail, Globe } from 'lucide-react';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';

interface ApplicationCardProps {
  application: Application;
  onClick: () => void;
}

const sourceIcons: Record<JobSource, React.ReactNode> = {
  linkedin: <Linkedin className="w-4 h-4 text-blue-600" />,
  naukri: <Globe className="w-4 h-4 text-blue-500" />,
  indeed: <Globe className="w-4 h-4 text-blue-700" />,
  manual: <Mail className="w-4 h-4 text-gray-500" />,
  unknown: <Mail className="w-4 h-4 text-gray-400" />,
};

const sourceLabels: Record<JobSource, string> = {
  linkedin: 'LinkedIn',
  naukri: 'Naukri',
  indeed: 'Indeed',
  manual: 'Manual',
  unknown: 'Unknown',
};

export function ApplicationCard({ application, onClick }: ApplicationCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: application.id.toString() });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      onClick={onClick}
      className={cn(
        'bg-white rounded-lg shadow-sm border border-gray-200 p-4 cursor-grab',
        'hover:shadow-md hover:border-blue-300 transition-all',
        isDragging && 'opacity-50 cursor-grabbing shadow-lg'
      )}
    >
      {/* Company & Position */}
      <div className="mb-3">
        <div className="flex items-start justify-between">
          <h4 className="font-semibold text-gray-900 line-clamp-1">
            {application.company_name}
          </h4>
          <div className="flex-shrink-0 ml-2" title={sourceLabels[application.source]}>
            {sourceIcons[application.source]}
          </div>
        </div>
        <p className="text-sm text-gray-600 mt-1 line-clamp-2">
          {application.position_title}
        </p>
      </div>

      {/* Details */}
      <div className="space-y-2">
        {application.location && (
          <div className="flex items-center text-xs text-gray-500">
            <MapPin className="w-3 h-3 mr-1" />
            <span className="truncate">{application.location}</span>
          </div>
        )}

        {application.salary_range && (
          <div className="flex items-center text-xs text-gray-500">
            <Building2 className="w-3 h-3 mr-1" />
            <span>{application.salary_range}</span>
          </div>
        )}

        <div className="flex items-center text-xs text-gray-400">
          <Calendar className="w-3 h-3 mr-1" />
          <span>{format(new Date(application.applied_date), 'MMM d, yyyy')}</span>
        </div>
      </div>

      {/* Notes indicator */}
      {application.notes && (
        <div className="mt-3 pt-2 border-t border-gray-100">
          <p className="text-xs text-gray-500 line-clamp-2">{application.notes}</p>
        </div>
      )}
    </div>
  );
}
