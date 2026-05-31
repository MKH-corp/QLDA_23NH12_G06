import type { BoardStatus } from '../types/task';

export const BOARD_COLUMNS: Array<{ key: BoardStatus; title: string }> = [
  { key: 'todo', title: 'Cần làm' },
  { key: 'doing', title: 'Đang làm' },
  { key: 'in_review', title: 'Chờ duyệt' },
  { key: 'blocked', title: 'Bị chặn' },
  { key: 'done', title: 'Hoàn thành' },
];
