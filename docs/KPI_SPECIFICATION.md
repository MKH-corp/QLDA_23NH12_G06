# Đặc tả KPI MVP

Tài liệu này chốt quy tắc KPI áp dụng cho MVP. Mọi thay đổi công thức phải cập nhật tài liệu, dữ liệu seed và test hồi quy trong cùng một commit.

## 1. Phạm vi

- KPI cá nhân được tính theo tháng nghiệp vụ với múi giờ `Asia/Ho_Chi_Minh`.
- Chỉ task ở trạng thái `done` và có `done_at` thuộc tháng đang tính mới đóng góp điểm.
- Tiến độ project và KPI cá nhân là hai chỉ số khác nhau. Tiến độ project không tự cộng điểm KPI.

## 2. Nguồn trọng số

Điểm task dùng `base_weight`, không dùng `estimated_hours` hoặc `actual_hours`.

| Trường | Mục đích | Ảnh hưởng KPI |
| --- | --- | --- |
| `task.base_weight` | Độ quan trọng của task, từ `1` đến `10` | Có |
| `task.estimated_hours` | Lập kế hoạch và workload | Không |
| `task.actual_hours` | Theo dõi thời gian thực tế | Không |
| `project.project_weight` | Hệ số ưu tiên project, từ `0.1` đến `10` | Có |

## 3. Công thức

Với mỗi task hoàn thành:

```text
base_score = task.base_weight * BASE_COMPLETION

if done_at <= deadline:
    task_score = base_score * ON_TIME_BONUS
else:
    task_score = base_score * OVERDUE_PENALTY

task_score = task_score + (task.reopen_count * REOPEN_PENALTY)
contributed_score = max(task_score * project.project_weight, 0)
```

Nếu task không thuộc project thì `project_weight = 1`. Nếu task không có deadline thì không cộng thưởng đúng hạn và không phạt trễ.

Giá trị seed mặc định:

| Rule | Giá trị | Ý nghĩa |
| --- | ---: | --- |
| `BASE_COMPLETION` | `1.0` | Điểm cơ sở theo `base_weight` |
| `ON_TIME_BONUS` | `1.2` | Hoàn thành đúng hạn được nhân `1.2` |
| `OVERDUE_PENALTY` | `0.5` | Hoàn thành trễ chỉ nhận `50%` điểm cơ sở |
| `REOPEN_PENALTY` | `-5.0` | Mỗi lần reopen trừ `5` điểm trước khi nhân `project_weight` |

## 4. Reopen và review

- Task có reviewer phải chuyển sang `in_review` trước khi chuyển sang `done`.
- Chỉ reviewer, admin hoặc người quản lý task hợp lệ mới được duyệt `in_review -> done`.
- Chỉ các vai trò trên được trả task `in_review -> todo|doing`.
- Reopen tăng khi task `done` bị mở lại hoặc reviewer trả task từ `in_review`.

## 5. Quyền sửa dữ liệu

| Dữ liệu | Admin | Manager phòng ban | Project manager / team lead | Staff assignee |
| --- | --- | --- | --- | --- |
| `base_weight`, deadline, assignee, reviewer | Sửa | Sửa trong phạm vi | Sửa trong project | Không |
| `estimated_hours` | Sửa | Sửa trong phạm vi | Sửa trong project | Không |
| `actual_hours` | Sửa | Sửa trong phạm vi | Sửa trong project | Sửa task của mình |
| `project_weight` | Sửa | Sửa project thuộc phòng ban | Sửa project được quản lý | Không |
| Gửi task sang `in_review` | Có | Có | Có | Có, với task của mình |
| Duyệt hoặc trả task review | Có | Có, trong phạm vi | Có, trong project | Có nếu là reviewer |

Mọi thay đổi `project_weight` phải được ghi audit log. `estimated_hours` không được dùng làm điểm để tránh tăng KPI bằng cách nâng giờ ước tính.

## 6. Tiến độ project

- Nếu project có task và milestone: `progress = task_score * 70% + milestone_score * 30%`.
- Nếu project chỉ có task: `progress = task_score * 100%`.
- Nếu project chỉ có milestone: `progress = milestone_score * 100%`.
- Nếu project chưa có task và milestone: `progress = 0%`.

Penalty tiến độ project được tính riêng theo task quá hạn, blocked và reopen. Các penalty này không thay thế rule KPI cá nhân.
