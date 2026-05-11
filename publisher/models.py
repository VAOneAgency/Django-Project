from django.db import models


from django.contrib.auth.models import AbstractUser


class Staff(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Uses Django's built-in session-based authentication.
    is_admin maps to is_staff (Django built-in superuser flag).
    USERNAME_FIELD remains 'username'; email is also stored.
    """
    is_admin = models.BooleanField(default=False)

    class Meta:
        db_table = 'tblstaff'

    def __str__(self):
        return self.email or self.username

    def save(self, *args, **kwargs):
        # Keep is_staff in sync with is_admin for Django admin access
        if self.is_admin:
            self.is_staff = True
        super().save(*args, **kwargs)


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_system = models.BooleanField(default=False)

    class Meta:
        db_table = 'tblroles'

    def __str__(self):
        return self.name


class StaffRoleAssignment(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='role_assignments')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='staff_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tblstaff_role_assignments'
        unique_together = ('staff', 'role')

    def __str__(self):
        return f"{self.staff.email} -> {self.role.name}"


class RolePermission(models.Model):
    role = models.OneToOneField(Role, on_delete=models.CASCADE, related_name='permissions')
    can_manage_accounts = models.BooleanField(default=False)
    can_delete_post = models.BooleanField(default=False)
    can_edit_own_post = models.BooleanField(default=True)

    class Meta:
        db_table = 'tblrole_permissions'

    def __str__(self):
        return f"Permissions for {self.role.name}"


class Organization(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)

    class Meta:
        db_table = 'tblorganizations'

    def __str__(self):
        return self.name


PLATFORM_CHOICES = [
    ('instagram', 'Instagram'),
    ('facebook', 'Facebook'),
    ('twitter', 'Twitter/X'),
    ('linkedin', 'LinkedIn'),
    ('tiktok', 'TikTok'),
]

ACCOUNT_STATUS_CHOICES = [
    ('active', 'Active'),
    ('expired', 'Token Expired'),
    ('disconnected', 'Disconnected'),
]


class SocialAccount(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='social_accounts')
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES)

    # Display / identity
    account_name = models.CharField(max_length=255, blank=True, help_text="e.g. @handle or Page name")
    account_id = models.CharField(max_length=255, blank=True, help_text="Platform user/page/business ID")

    # Tokens
    access_token = models.TextField(help_text="User or Page access token")
    token_expires_at = models.DateTimeField(null=True, blank=True)

    # Instagram / Facebook specific
    app_id = models.CharField(max_length=100, blank=True, help_text="Meta App ID")
    app_secret = models.CharField(max_length=255, blank=True, help_text="Meta App Secret — keep private")
    page_id = models.CharField(max_length=100, blank=True, help_text="Facebook Page ID (required for Instagram Business)")
    ig_business_account_id = models.CharField(max_length=100, blank=True, help_text="Instagram Business Account ID")

    # Permissions granted
    permissions_granted = models.TextField(blank=True, help_text="Comma-separated list of approved permissions")

    # Status
    status = models.CharField(max_length=20, choices=ACCOUNT_STATUS_CHOICES, default='active')
    connected_at = models.DateTimeField(auto_now_add=True, null=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'tblsocial_accounts'
        ordering = ['platform', 'account_name']

    def __str__(self):
        label = self.account_name or self.account_id or "—"
        return f"{self.organization.name} · {self.get_platform_display()} ({label})"

    @property
    def is_instagram(self):
        return self.platform == 'instagram'

    @property
    def is_facebook(self):
        return self.platform == 'facebook'

    @property
    def display_permissions(self):
        return [p.strip() for p in self.permissions_granted.split(',') if p.strip()]


POST_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('scheduled', 'Scheduled'),
    ('published', 'Published'),
    ('failed', 'Failed'),
]


class Post(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='posts')
    created_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, related_name='posts')
    caption = models.TextField()
    status = models.CharField(max_length=20, choices=POST_STATUS_CHOICES, default='draft')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tblposts'
        ordering = ['-created_at']

    def __str__(self):
        return f"Post #{self.id} - {self.organization.name} ({self.status})"


PLATFORM_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('published', 'Published'),
    ('failed', 'Failed'),
]


class PostPlatform(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='platforms')
    social_account = models.ForeignKey(SocialAccount, on_delete=models.CASCADE, related_name='post_platforms')
    status = models.CharField(max_length=20, choices=PLATFORM_STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    published_post_id = models.CharField(max_length=255, blank=True, help_text="ID returned by platform after successful publish")

    class Meta:
        db_table = 'tblpost_platforms'

    def __str__(self):
        return f"Post #{self.post_id} -> {self.social_account}"


class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='images')
    image_url = models.URLField(max_length=1000)
    sort_order = models.PositiveIntegerField(default=0)
    media_type = models.CharField(max_length=10, default='image', choices=[('image', 'Image'), ('video', 'Video')])

    class Meta:
        db_table = 'tblpost_images'
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.media_type.title()} for Post #{self.post_id} (order {self.sort_order})"


class WebhookEvent(models.Model):
    """
    Stores incoming webhook events from Meta (Instagram / Facebook).
    Received at POST /webhooks/meta/
    """
    PLATFORM_CHOICES = [
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
    ]
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default='instagram')
    object_type = models.CharField(max_length=100, blank=True, help_text="e.g. 'instagram', 'page'")
    entry_id = models.CharField(max_length=255, blank=True, help_text="ID of the object that triggered the event")
    field = models.CharField(max_length=100, blank=True, help_text="Webhook field subscribed to, e.g. 'comments', 'messages'")
    raw_payload = models.TextField(help_text="Full JSON payload from Meta")
    received_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)

    class Meta:
        db_table = 'tblwebhook_events'
        ordering = ['-received_at']

    def __str__(self):
        return f"{self.platform} {self.field} event @ {self.received_at:%Y-%m-%d %H:%M}"
