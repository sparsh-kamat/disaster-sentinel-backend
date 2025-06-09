from django.core.mail import send_mail
from django.conf import settings
from users.models import CustomUser  # Correct import

def send_disaster_email_alert_to_state_users(disaster_data, test_email=None):
    """
    Send email alerts to users in the same state as the disaster.
    Only sends for alertlevel 'orange' or 'red'.
    If no users are found, sends to test_email if provided.
    """
    state = disaster_data.get("state")
    alertlevel = disaster_data.get("alertlevel", "").lower()
    if not state or alertlevel not in ("orange", "red"):
        return

    users_in_state = CustomUser.objects.filter(state__iexact=state).exclude(email="").values_list("email", flat=True)
    recipient_list = list(users_in_state)

    if not recipient_list and test_email:
        recipient_list = [test_email]
    if not recipient_list:
        return

    subject = f"[Disaster Sentinel] Urgent Alert: {disaster_data.get('title')} in {state} (Alert Level: {disaster_data.get('alertlevel')})"
    message = (
        "Dear User,\n\n"
        "We wish to inform you that a disaster event has been detected in your state.\n\n"
        f"Event Details:\n"
        f"- Disaster Type: {disaster_data.get('title')}\n"
        f"- Location: {state}\n"
        f"- More Information: {disaster_data.get('link')}\n\n"
        "Please stay alert and follow guidance from local authorities. Your safety is our priority.\n\n"
        "Best regards,\n"
        "Disaster Sentinel Team"
    )

    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        recipient_list,
        fail_silently=False,
    )