interface PaginationControlsProps {
  page: number;
  pages: number;
  total: number;
  onPageChange: (page: number) => void;
}

export function PaginationControls({ page, pages, total, onPageChange }: PaginationControlsProps) {
  if (pages <= 1) return null;

  return (
    <div className="pagination">
      <button type="button" className="button-secondary" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
        Trang trước
      </button>
      <span>
        Trang {page}/{pages} · {total} bản ghi
      </span>
      <button type="button" className="button-secondary" disabled={page >= pages} onClick={() => onPageChange(page + 1)}>
        Trang sau
      </button>
    </div>
  );
}
