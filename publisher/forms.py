from django import forms
from .models import (Staff, Role, StaffRoleAssignment, RolePermission,
                     Organization, SocialAccount, Post, PostPlatform, PostImage)


class StaffForm(forms.ModelForm):
    """
    Staff creation/edit form using Django's built-in password hashing
    via set_password(). Works with AbstractUser.
    """
    password = forms.CharField(
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text="Leave blank to keep current password."
    )

    class Meta:
        model = Staff
        fields = ['username', 'email', 'is_admin']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Unique username for login'}),
        }

    def save(self, commit=True):
        staff = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            staff.set_password(password)  # Django's built-in secure hashing
        elif not staff.pk:
            # New staff with no password — set unusable password
            staff.set_unusable_password()
        # Sync is_staff with is_admin for Django admin access
        staff.is_staff = staff.is_admin
        if commit:
            staff.save()
        return staff


class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ['name', 'is_system']


class RolePermissionForm(forms.ModelForm):
    class Meta:
        model = RolePermission
        fields = ['can_manage_accounts', 'can_delete_post', 'can_edit_own_post']


class StaffRoleAssignmentForm(forms.ModelForm):
    class Meta:
        model = StaffRoleAssignment
        fields = ['staff', 'role']


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name', 'slug']
        widgets = {
            'slug': forms.TextInput(attrs={'placeholder': 'e.g. my-organization'}),
        }


class SocialAccountBaseForm(forms.ModelForm):
    """Shared base — always shown regardless of platform."""
    class Meta:
        model = SocialAccount
        fields = ['organization', 'platform', 'account_name', 'account_id', 'access_token', 'status']
        widgets = {
            'access_token': forms.PasswordInput(render_value=True,
                attrs={'placeholder': 'Paste your access token here', 'autocomplete': 'off'}),
            'account_id': forms.TextInput(attrs={'placeholder': 'Platform user/page ID'}),
            'account_name': forms.TextInput(attrs={'placeholder': '@handle or Page name'}),
        }


class InstagramAccountForm(forms.ModelForm):
    """Full form for Instagram Business connections."""
    class Meta:
        model = SocialAccount
        fields = [
            'organization', 'account_name', 'account_id',
            'access_token', 'app_id', 'app_secret',
            'page_id', 'ig_business_account_id',
            'permissions_granted', 'status',
        ]
        widgets = {
            'access_token': forms.PasswordInput(render_value=True,
                attrs={'placeholder': 'User access token from Meta', 'autocomplete': 'off'}),
            'app_secret': forms.PasswordInput(render_value=True,
                attrs={'placeholder': 'App Secret — keep private', 'autocomplete': 'off'}),
            'app_id': forms.TextInput(attrs={'placeholder': 'e.g. 2460738144394548'}),
            'page_id': forms.TextInput(attrs={'placeholder': 'Facebook Page ID'}),
            'ig_business_account_id': forms.TextInput(attrs={'placeholder': 'Instagram Business Account ID'}),
            'account_name': forms.TextInput(attrs={'placeholder': '@handle or display name'}),
            'account_id': forms.TextInput(attrs={'placeholder': 'Instagram user ID'}),
            'permissions_granted': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'instagram_basic, instagram_content_publishing, pages_read_engagement, business_management, pages_show_list',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-fill recommended permissions
        if not self.instance.pk:
            self.fields['permissions_granted'].initial = (
                'instagram_basic, instagram_content_publishing, '
                'pages_read_engagement, business_management, pages_show_list'
            )


class FacebookAccountForm(forms.ModelForm):
    """Form for Facebook Page connections."""
    class Meta:
        model = SocialAccount
        fields = [
            'organization', 'account_name', 'account_id',
            'access_token', 'app_id', 'app_secret',
            'page_id', 'permissions_granted', 'status',
        ]
        widgets = {
            'access_token': forms.PasswordInput(render_value=True,
                attrs={'placeholder': 'Page access token', 'autocomplete': 'off'}),
            'app_secret': forms.PasswordInput(render_value=True,
                attrs={'placeholder': 'App Secret', 'autocomplete': 'off'}),
            'app_id': forms.TextInput(attrs={'placeholder': 'Meta App ID'}),
            'page_id': forms.TextInput(attrs={'placeholder': 'Facebook Page ID'}),
            'account_name': forms.TextInput(attrs={'placeholder': 'Page name'}),
            'account_id': forms.TextInput(attrs={'placeholder': 'Facebook user/page ID'}),
            'permissions_granted': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'pages_manage_posts, pages_read_engagement, pages_show_list, business_management',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['permissions_granted'].initial = (
                'pages_manage_posts, pages_read_engagement, pages_show_list, business_management'
            )


class GenericAccountForm(forms.ModelForm):
    """Twitter, LinkedIn, TikTok."""
    class Meta:
        model = SocialAccount
        fields = ['organization', 'platform', 'account_name', 'account_id', 'access_token', 'status']
        widgets = {
            'access_token': forms.PasswordInput(render_value=True,
                attrs={'placeholder': 'Access token', 'autocomplete': 'off'}),
            'account_name': forms.TextInput(attrs={'placeholder': '@handle or display name'}),
            'account_id': forms.TextInput(attrs={'placeholder': 'Platform user ID'}),
        }


def get_account_form(platform, *args, **kwargs):
    """Return the right form class for the given platform."""
    if platform == 'instagram':
        return InstagramAccountForm(*args, **kwargs)
    elif platform == 'facebook':
        return FacebookAccountForm(*args, **kwargs)
    else:
        return GenericAccountForm(*args, **kwargs)


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        # published_at is system-managed — never edited directly by user
        fields = ['organization', 'created_by', 'caption', 'status', 'scheduled_at']
        widgets = {
            'caption': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Write your caption here…'}),
            'scheduled_at': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['scheduled_at'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['scheduled_at'].required = False

    def clean(self):
        cleaned = super().clean()
        status = cleaned.get('status')
        scheduled_at = cleaned.get('scheduled_at')
        # Enforce: if scheduled status chosen, scheduled_at must be set and in the future
        if status == 'scheduled' and not scheduled_at:
            self.add_error('scheduled_at', 'A future date and time is required when status is Scheduled.')
        if status == 'scheduled' and scheduled_at:
            from django.utils import timezone
            if scheduled_at <= timezone.now():
                self.add_error('scheduled_at', 'Scheduled time must be in the future.')
        return cleaned


class PostPlatformForm(forms.ModelForm):
    class Meta:
        model = PostPlatform
        fields = ['post', 'social_account', 'status', 'error_message']
        widgets = {'error_message': forms.Textarea(attrs={'rows': 2})}


class PostImageForm(forms.ModelForm):
    class Meta:
        model = PostImage
        fields = ['post', 'image_url', 'sort_order', 'media_type']
