import { Card, CardHeader, CardContent } from '~/components/ui/card';

interface CitationCardProps {
  id: string;
  source: string;
  heading: string;
  text: string;
  score: number;
  onClick?: () => void;
}

export function CitationCard({ source, heading, text, score, onClick }: CitationCardProps) {
  const percent = Math.round(score * 100);

  return (
    <Card
      onClick={onClick}
      className="cursor-pointer hover:border-gray-600 transition-colors"
    >
      <CardHeader className="flex flex-row items-center justify-between space-y-0 p-3 pb-1">
        <span className="text-xs font-mono text-gray-400 truncate" title={source}>
          {source}
        </span>
        <span className="text-xs text-gray-500">{percent}% match</span>
      </CardHeader>
      <CardContent className="p-3 pt-1">
        {heading && (
          <div className="text-xs text-gray-500 truncate mb-1" title={heading}>
            {heading}
          </div>
        )}
        <p className="text-sm text-gray-300 line-clamp-3">{text}</p>
      </CardContent>
    </Card>
  );
}
