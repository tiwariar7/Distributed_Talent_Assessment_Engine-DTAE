"""JWT token serializers using email as the login identifier."""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Accept ``email`` instead of ``username`` in the token request body."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields.pop("username", None)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Retrieve active memberships
        memberships = user.memberships.select_related("organization", "role").all()

        # Inject user context and role-memberships matrix
        token["email"] = user.email
        token["first_name"] = user.first_name
        token["last_name"] = user.last_name
        token["memberships"] = [
            {
                "org_slug": m.organization.slug,
                "org_name": m.organization.name,
                "role_code": m.role.code
            }
            for m in memberships
        ]

        return token

    def validate(self, attrs: dict) -> dict:
        """Map email to Django's username field for authentication."""
        email = attrs.get("email", "").lower()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError("Invalid credentials.") from exc

        attrs["username"] = user.username
        return super().validate(attrs)
