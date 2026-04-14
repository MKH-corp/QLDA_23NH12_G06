import type { BoardStatus } from '../types/task';

export const BOARD_COLUMNS: Array<{ key: BoardStatus; title: string }> = [
  { key: 'todo', title: 'Todo' },
  { key: 'doing', title: 'Doing' },
  { key: 'done', title: 'Done' },
  { key: 'blocked', title: 'Blocked' },
];
