from django.conf import settings
from django.core.mail import send_mail


def send_email(subject: str, message: str, to_email: str) -> int:
    return send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
        recipient_list=[to_email],
        fail_silently=False,
    )
