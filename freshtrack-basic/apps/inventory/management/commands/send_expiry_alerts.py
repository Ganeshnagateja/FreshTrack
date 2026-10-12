from datetime import timedelta

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Organization, User
from apps.inventory.models import ExpiryAlert, InventoryItem


class Command(BaseCommand):
    help = "Send a daily email digest for items that are expired or inside their category expiry-alert window."

    def handle(self, *args, **options):
        today = timezone.localdate()
        organizations_processed = 0
        digests_sent = 0
        self.stdout.write(f"Checking inventory expiry alerts for {today.isoformat()}…")

        for organization in Organization.objects.all().iterator():
            organizations_processed += 1
            candidates = InventoryItem.objects.filter(
                organization=organization,
                status=InventoryItem.Status.ACTIVE,
                expiry_date__isnull=False,
            ).select_related("category")
            due = []
            for item in candidates:
                days_left = (item.expiry_date - today).days
                if days_left < 0:
                    kind = ExpiryAlert.Kind.EXPIRED
                elif days_left <= item.effective_alert_days:
                    kind = ExpiryAlert.Kind.EXPIRING
                else:
                    continue
                already_logged = ExpiryAlert.objects.filter(
                    item=item, alert_date=today, kind=kind
                ).exists()
                if not already_logged:
                    due.append((item, kind, days_left))

            if not due:
                continue
            recipients = list(
                User.objects.filter(organization=organization, is_active=True)
                .exclude(email="")
                .values_list("email", flat=True)
                .distinct()
            )
            if not recipients:
                self.stdout.write(self.style.WARNING(
                    f"Skipped {organization.name}: no active workspace user has an email address."
                ))
                continue

            lines = [
                f"FreshTrack expiry digest — {organization.name}",
                f"Date: {today.isoformat()}",
                "",
                "Review the following stock items:",
            ]
            for item, kind, days_left in due:
                if kind == ExpiryAlert.Kind.EXPIRED:
                    status = f"EXPIRED {abs(days_left)} day(s) ago"
                elif days_left == 0:
                    status = "expires today"
                elif days_left == 1:
                    status = "expires tomorrow"
                else:
                    status = f"expires in {days_left} day(s)"
                lines.append(
                    f"- {item.name} | {item.quantity} {item.unit} | {status} | {item.category.name}"
                )
            lines.extend(["", "This digest is based on the expiry dates recorded in FreshTrack."])
            try:
                sent = send_mail(
                    subject=f"FreshTrack: {len(due)} expiry alert(s) for {organization.name}",
                    message="\n".join(lines),
                    from_email=None,
                    recipient_list=recipients,
                    fail_silently=False,
                )
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f"Email failed for {organization.name}: {exc}"))
                continue
            if sent:
                with transaction.atomic():
                    ExpiryAlert.objects.bulk_create(
                        [ExpiryAlert(organization=organization, item=item, alert_date=today, kind=kind) for item, kind, _ in due],
                        ignore_conflicts=True,
                    )
                digests_sent += 1
                self.stdout.write(self.style.SUCCESS(
                    f"Sent {len(due)} alert(s) for {organization.name} to {len(recipients)} recipient(s)."
                ))
            else:
                self.stderr.write(self.style.WARNING(f"No email sent for {organization.name}; alert entries were not recorded."))

        self.stdout.write(self.style.SUCCESS(
            f"Finished. Workspaces checked: {organizations_processed}; digests sent: {digests_sent}."
        ))
