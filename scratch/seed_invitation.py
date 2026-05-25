import os
import sys
import django
from django.utils import timezone
from datetime import timedelta

# Add backend root to path
sys.path.append("/app")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from apps.assessments.models import Assessment, AssessmentInvitation

User = get_user_model()

def seed_invitation():
    try:
        user = User.objects.get(email="candidate@demo.test")
        assessment = Assessment.objects.get(pk=1)
        
        # Delete existing invitation if any
        AssessmentInvitation.objects.filter(email=user.email, assessment=assessment).delete()
        AssessmentInvitation.objects.filter(token="demo-candidate-token").delete()
        
        invite = AssessmentInvitation.objects.create(
            assessment=assessment,
            email=user.email,
            user=user,
            token="demo-candidate-token",
            expires_at=timezone.now() + timedelta(days=7),
            scheduled_start=timezone.now(),
            instructions="Please complete all sections. Ensure your webcam and screen sharing are active.",
            proctoring_required=True,
            status=AssessmentInvitation.InvitationStatus.PENDING,
            is_active=True
        )
        print(f"Successfully seeded invitation:")
        print(f"  ID: {invite.id}")
        print(f"  Token: {invite.token}")
        print(f"  User: {invite.email}")
        print(f"  Assessment: {invite.assessment.title}")
    except Exception as e:
        print(f"Failed to seed invitation: {e}")

if __name__ == "__main__":
    seed_invitation()
