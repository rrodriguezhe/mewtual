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

## 2. Observer — `Match` acceptance auto-creates its `Chat`

**Where:** `Final-Project/backend/chat/signals.py` (`crear_chat_al_aceptar`), wired up in
`Final-Project/backend/chat/apps.py` (`ChatConfig.ready()`).

**Problem:** When a `Match` becomes mutual (`estado → "ACEPTADO"`), HU-09 requires that both
users get a chat enabled between them, without either of them taking an extra action. The
`matching` app owns the swipe/accept flow and shouldn't need to know about `chat`'s models to
satisfy this — `matching` → `chat` is a one-directional dependency (see Architecture in
`CLAUDE.md`), so `Match` can't call into `Chat` creation directly without inverting that.

**Solution:** `matching`'s `Match` model is the subject; it just saves itself and knows nothing
about chats. `chat` subscribes as an observer via Django's signal dispatcher:
```python
@receiver(post_save, sender=Match)
def crear_chat_al_aceptar(sender, instance, **kwargs):
    if instance.estado == "ACEPTADO":
        Chat.objects.get_or_create(match=instance)
```
Any `Match` save that flips `estado` to `"ACEPTADO"` triggers chat creation automatically —
`get_or_create` keeps it idempotent if the match is saved again while already accepted. The
dependency stays one-directional: `chat` imports `matching.models.Match`, never the reverse.

**Tests:** `Final-Project/backend/matching/tests.py`,
`test_like_with_incoming_pending_match_becomes_mutual` (mutual like flips a match to
`ACEPTADO` and asserts the `Chat` now exists), alongside the negative cases in the same file —
`test_like_with_no_incoming_match_creates_pending_match` (still `PENDIENTE`, no chat yet) and
`test_rechazar_with_incoming_pending_match_marks_it_rechazado` (`RECHAZADO`, no chat created).
