import re
from django.core.exceptions import ValidationError
from django.core.validators import validate_email as django_validate_email
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password as django_validate_password


# RFC 5322 compatible practical email regex
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
)


def validate_email_format(email: str) -> str:
    """
    Validates email format, domain structure, and length.
    Returns normalized (lowercased and stripped) email.
    """
    if not email:
        raise ValidationError("Email address is required.")

    email = email.strip()

    if len(email) > 254:
        raise ValidationError("Email address cannot exceed 254 characters.")

    # 1. Django's standard validate_email
    try:
        django_validate_email(email)
    except ValidationError:
        raise ValidationError("Enter a valid email address (e.g. name@example.com).")

    # 2. Comprehensive regex format check
    if not EMAIL_REGEX.match(email):
        raise ValidationError("Enter a valid email format (e.g. name@example.com).")

    # 3. Domain-specific checks
    try:
        local_part, domain_part = email.rsplit('@', 1)
    except ValueError:
        raise ValidationError("Email must contain exactly one '@' symbol.")

    if not domain_part or '.' not in domain_part:
        raise ValidationError("Email must include a valid domain name (e.g. example.com).")

    domain_segments = domain_part.split('.')
    # Check top-level domain
    tld = domain_segments[-1]
    if len(tld) < 2 or not tld.isalpha():
        raise ValidationError("The email domain extension must contain at least 2 letters (e.g. .com, .org).")

    # Reject consecutive dots in local or domain part
    if '..' in email:
        raise ValidationError("Email address cannot contain consecutive periods.")

    return email.lower()


def validate_unique_email(email: str, exclude_user_id=None) -> None:
    """
    Checks if email already exists in User database, ignoring case.
    Can exclude a user id when updating profile.
    """
    normalized_email = email.strip().lower()
    qs = User.objects.filter(email__iexact=normalized_email)
    if exclude_user_id:
        qs = qs.exclude(pk=exclude_user_id)

    if qs.exists():
        raise ValidationError("An account with this email address is already registered.")


def validate_password_strength(password: str, user=None) -> list[str]:
    """
    Validates password against complexity rules and Django's built-in auth validators.
    Returns a list of error message strings (empty if valid).
    """
    errors = []

    if not password:
        return ["Password cannot be empty."]

    # 1. Minimum length
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    elif len(password) > 128:
        errors.append("Password cannot exceed 128 characters.")

    # 2. Uppercase check
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter (A-Z).")

    # 3. Lowercase check
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter (a-z).")

    # 4. Digit check
    if not re.search(r'[0-9]', password):
        errors.append("Password must contain at least one number (0-9).")

    # 5. Special character check
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?~`]', password):
        errors.append("Password must contain at least one special character (e.g. !@#$%^&*).")

    # 6. Django's built-in validators (similarity, common passwords, numeric)
    try:
        django_validate_password(password, user=user)
    except ValidationError as e:
        for msg in e.messages:
            if msg not in errors:
                errors.append(msg)

    return errors


def validate_phone_number(phone: str, required: bool = True) -> str:
    """
    Validates phone number:
    - Checks required state and whitespace trimming
    - Allows digits, spaces, hyphens (-), parentheses, and optional leading '+'
    - Enforces 10 to 15 digits (standard E.164 and local mobile numbers)
    - Rejects all-identical digits (e.g. 0000000000, 1111111111)
    - Rejects 10-digit mobile numbers starting with '0'
    Returns cleaned phone string.
    """
    if not phone:
        if required:
            raise ValidationError("Phone number is required.")
        return ""

    phone = phone.strip()

    # Allowed characters: digits, spaces, hyphens, parentheses, and optional leading plus sign
    if not re.match(r"^\+?[0-9\s\-()]+$", phone):
        raise ValidationError("Phone number can only contain digits, spaces, dashes (-), parentheses, and an optional leading '+'.")

    # Extract pure digits
    digits = re.sub(r"\D", "", phone)

    if len(digits) < 10:
        raise ValidationError("Phone number is too short. Please enter a valid phone number with at least 10 digits.")

    if len(digits) > 15:
        raise ValidationError("Phone number cannot exceed 15 digits.")

    if len(set(digits)) == 1:
        raise ValidationError("Please enter a valid active phone number (cannot be all identical digits).")

    # If it is a 10-digit number without country code, it should not start with 0
    if len(digits) == 10 and digits.startswith('0'):
        raise ValidationError("A 10-digit mobile number cannot start with 0.")

    return phone
