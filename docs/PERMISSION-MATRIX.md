# 学院权限矩阵（6 个角色 × 11 个权限点）

> 由 `scripts/export_matrix.py` 从 `config/academy_permissions.json` 生成，不要手改。
> 图例：✓ = 允许；— = 无权限；✓（本人）= 仅本人负责的会员；✓（脱敏）= 手机号后 4 位。

| 权限点 | 运营专员 | 运营主管 | 会员经理 | 前台接待 | 系统管理员 | 审计员 |
|---|---|---|---|---|---|---|
| `academy.course.read` | ✓ | ✓ | ✓ | ✓ | — | — |
| `academy.course.edit` | ✓ | ✓ | — | — | — | — |
| `academy.course.publish` | — | ✓ | — | — | — | — |
| `academy.session.manage` | ✓ | ✓ | — | — | — | — |
| `academy.instructor.manage` | ✓ | ✓ | — | — | — | — |
| `academy.application.review` | ✓ | ✓ | — | — | — | — |
| `academy.roster.read` | ✓ | ✓ | ✓（本人） | ✓（脱敏） | — | — |
| `academy.learning.correct` | ✓ | ✓ | — | — | — | — |
| `academy.review.moderate` | ✓ | ✓ | — | — | — | — |
| `academy.stats.read` | — | ✓ | ✓ | — | — | — |
| `academy.entitlement.config` | — | ✓ | — | — | — | — |

统计：11 个权限点；运营专员 8 个、运营主管 11 个、会员经理 3 个、前台接待 2 个、系统管理员 0 个、审计员 0 个。

数据范围：会员经理的 `academy.roster.read` 只返回 `manager_id = 当前用户` 的会员；前台接待返回的手机号只保留后 4 位。
