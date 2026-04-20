interface Column<T> {
  key: string;
  title: string;
  render: (item: T) => React.ReactNode;
}

interface DataTableProps<T> {
  title: string;
  items: T[];
  columns: Array<Column<T>>;
  emptyText: string;
}

export function DataTable<T>({ title, items, columns, emptyText }: DataTableProps<T>) {
  return (
    <section className="panel">
      <div className="panel__header">
        <h2>{title}</h2>
      </div>

      {items.length === 0 ? (
        <div className="panel-empty">{emptyText}</div>
      ) : (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                {columns.map((column) => (
                  <th key={column.key}>{column.title}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.map((item, index) => (
                <tr key={index}>
                  {columns.map((column) => (
                    <td key={column.key}>{column.render(item)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
