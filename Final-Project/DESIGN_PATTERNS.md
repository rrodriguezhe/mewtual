# Design Patterns

Notes for the "design patterns" section of `final-report.pdf`. Each team member should add
their pattern here as it's implemented, with a short justification tied to real code — not
retrofitted after the fact.

## 1. Strategy — request authorization in `reports` and `adoption`

**Where:** `Final-Project/backend/adoption/views.py` (`IsGatoOwnerOrStaff`),
`Final-Project/backend/reports/views.py` (`ReportViewSet.get_permissions`), and
`Final-Project/backend/reports/serializers.py` (`ReportSerializer.get_fields`).

**Problem:** Both apps need different authorization rules depending on the action being
performed and who's asking — e.g. in `adoption`, reads should be open to any authenticated
user but writes restricted to the cat's owner or staff; in `reports`, only staff can transition
a report's `estado`, while anyone can file one. Hard-coding these checks as `if/elif` chains
inside the view methods would tie the authorization logic to the CRUD logic and make each rule
harder to test or swap independently.

**Solution:** Encapsulate each authorization rule as an interchangeable object behind a common
interface, selected at runtime:
- `IsGatoOwnerOrStaff(permissions.BasePermission)` implements DRF's `has_object_permission`
  interface — the "algorithm" (owner-or-staff-can-write, everyone-can-read) is swappable
  independently of the view that uses it.
- `ReportViewSet.get_permissions()` picks a different permission strategy
  (`IsAuthenticated` vs. `IsAdminUser`) depending on `self.action`, rather than branching
  inline in each method.
- `ReportSerializer.get_fields()` similarly swaps field-level read-only behavior (`estado`)
  based on the requester's role.

This is DRF's own `permission_classes` design (a well-known Strategy application) — reused
here rather than reinvented, and extended with `get_permissions()`/`get_fields()` for
per-action/per-role variation.

**Tests:** `Final-Project/backend/reports/tests.py` and
`Final-Project/backend/adoption/tests.py` exercise each strategy's outcome directly
(owner vs. non-owner vs. staff, per action).

## 2. (pending) — Observer, `matching` → `chat`

Tentatively assigned to the `matching`/`chat` owner: a `Match.estado → "ACEPTADO"` signal
auto-creating the corresponding `Chat`, satisfying HU-09 ("el sistema notifica a ambos
usuarios y habilita el chat entre ellos"). Not implemented yet — add notes here once it lands.
