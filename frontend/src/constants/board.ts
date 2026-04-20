import type { BoardStatus } from '../types/task';

export const BOARD_COLUMNS: Array<{ key: BoardStatus; title: string }> = [
  { key: 'todo', title: 'Todo' },
  { key: 'doing', title: 'Doing' },
  { key: 'blocked', title: 'Blocked' },
  { key: 'done', title: 'Done' },
];
