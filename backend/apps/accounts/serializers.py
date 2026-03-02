from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.utils.text import slugify
from apps.organizations.models import Organization
from .models import Membership, Role, User


class RegisterSerializer(serializers.Serializer):
    """
    Register a new user and attach them to an organization with a role.
    For recruiters, supports organization onboarding.
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    organization_slug = serializers.SlugField(required=False, allow_null=True)
    organization_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=["candidate", "recruiter"])
    invitation_token = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value: str) -> str:
        """Reject duplicate registrations."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate_password(self, value: str) -> str:
        """Apply Django password validators."""
        validate_password(value)
        return value

    def validate(self, attrs: dict) -> dict:
        role_code = attrs["role"]
        org_slug = attrs.get("organization_slug")
        org_name = attrs.get("organization_name")
        inv_token = attrs.get("invitation_token")

        try:
            attrs["role_obj"] = Role.objects.get(code=role_code)
        except Role.DoesNotExist as exc:
            raise serializers.ValidationError(
                {"role": f"Role '{role_code}' is not configured."},
            ) from exc

        # Org onboarding or linking
        if role_code == "recruiter":
            if inv_token:
                # Joining via invitation
                from .models import RecruiterInvitation
                try:
                    invitation = RecruiterInvitation.objects.get(
                        token=inv_token,
                        email__iexact=attrs["email"],
                        is_accepted=False
                    )
                    attrs["invitation_obj"] = invitation
                    attrs["organization"] = invitation.organization
                except RecruiterInvitation.DoesNotExist as exc:
                    raise serializers.ValidationError(
                        {"invitation_token": "Invalid or expired invitation token."},
                    ) from exc
            elif org_slug:
                # Join existing organization
                try:
                    attrs["organization"] = Organization.objects.get(slug=org_slug, is_active=True)
                except Organization.DoesNotExist as exc:
                    raise serializers.ValidationError(
                        {"organization_slug": "Organization not found or inactive."},
                    ) from exc
            elif org_name:
                # Create a new organization
                new_slug = slugify(org_name)
                if Organization.objects.filter(slug=new_slug).exists():
                    raise serializers.ValidationError(
                        {"organization_name": "An organization with this name/slug already exists."},
                    )
                attrs["organization_name_to_create"] = org_name
                attrs["organization_slug_to_create"] = new_slug
            else:
                raise serializers.ValidationError(
                    {"organization_name": "Organization name or slug is required for recruiters."},
                )
        else:
            # Candidate
            if inv_token:
                # Candidate joining via assessment invitation
                from apps.assessments.models import AssessmentInvitation
                try:
                    invitation = AssessmentInvitation.objects.select_related(
                        "assessment__organization"
                    ).get(
                        token=inv_token,
                        email__iexact=attrs["email"],
                        is_active=True
                    )
                    attrs["invitation_obj"] = invitation
                    attrs["organization"] = invitation.assessment.organization
                except AssessmentInvitation.DoesNotExist as exc:
                    raise serializers.ValidationError(
                        {"invitation_token": "Invalid or expired candidate invitation token."},
                    ) from exc
            elif org_slug:
                try:
                    attrs["organization"] = Organization.objects.get(slug=org_slug, is_active=True)
                except Organization.DoesNotExist as exc:
                    raise serializers.ValidationError(
                        {"organization_slug": "Organization not found or inactive."},
                    ) from exc
            else:
                # Decoupled candidate registering independently
                attrs["organization"] = None

        return attrs

    def create(self, validated_data: dict) -> User:
        """Create user and membership in a single logical transaction."""
        import uuid
        from datetime import datetime, timedelta, timezone
        from .models import VerificationToken

        # Handle Org creation if needed
        if "organization_name_to_create" in validated_data:
            org = Organization.objects.create(
                name=validated_data["organization_name_to_create"],
                slug=validated_data["organization_slug_to_create"],
                is_active=True,
            )
        else:
            org = validated_data.get("organization")

        role = validated_data["role_obj"]

        user = User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )
        
        if org:
            Membership.objects.get_or_create(user=user, organization=org, role=role)

        # Auto-link any other pending invitations matching candidate's email
        if role.code == "candidate":
            from apps.assessments.models import AssessmentInvitation
            pending_invitations = AssessmentInvitation.objects.filter(
                email__iexact=user.email,
            ).select_related("assessment__organization")
            
            for invitation in pending_invitations:
                invitation.user = user
                invitation.save(update_fields=["user"])
                
                # Ensure the candidate has a membership in the assessment's organization
                Membership.objects.get_or_create(
                    user=user,
                    organization=invitation.assessment.organization,
                    role=role,
                )

        # Mark invitation as accepted if relevant
        inv_obj = validated_data.get("invitation_obj")
        if inv_obj:
            if hasattr(inv_obj, "is_accepted"):
                inv_obj.is_accepted = True
            if hasattr(inv_obj, "is_active"):
                inv_obj.is_active = False
            if hasattr(inv_obj, "started_at") and not inv_obj.started_at:
                inv_obj.started_at = datetime.now(timezone.utc)
            inv_obj.save()

        # Generate Email Verification Token
        verify_token = uuid.uuid4().hex
        VerificationToken.objects.create(
            user=user,
            token=verify_token,
            token_type=VerificationToken.TokenType.VERIFICATION,
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )

        # Log link to server logs for testing in local environment
        print("\n" + "=" * 60)
        print(f"EMAIL VERIFICATION LINK: http://localhost/verify?token={verify_token}")
        print("=" * 60 + "\n")

        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Authenticated user's profile with organization memberships."""

    memberships = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "is_email_verified",
            "profile_image",
            "memberships",
        )
        read_only_fields = ("id", "email", "is_email_verified", "memberships")

    def get_memberships(self, user: User) -> list[dict]:
        """Return role and organization for each membership."""
        return [
            {
                "organization": membership.organization.slug,
                "organization_name": membership.organization.name,
                "role": membership.role.code,
            }
            for membership in user.memberships.select_related(
                "organization",
                "role",
            )
        ]

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Optimize imports and clean up code structure.

# Refactor: Optimize imports and clean up code structure.
