from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from .models import (Staff, Role, StaffRoleAssignment, RolePermission,
                     Organization, SocialAccount, Post, PostPlatform, PostImage)
from .forms import (StaffForm, RoleForm, RolePermissionForm, StaffRoleAssignmentForm,
                    OrganizationForm, InstagramAccountForm, FacebookAccountForm,
                    GenericAccountForm, PostForm, PostPlatformForm, PostImageForm)


# ─── Auth ─────────────────────────────────────────────────────────────────────

def login_view(request):
    """
    Custom login view using Django's built-in authenticate() and login().
    Supports login by email — looks up username from email first.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    error = None
    email = ''
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        # Django auth uses username; look up username from email
        try:
            staff_obj = Staff.objects.get(email__iexact=email)
            user = authenticate(request, username=staff_obj.username, password=password)
        except Staff.DoesNotExist:
            user = None
        if user is not None:
            login(request, user)
            messages.success(request, 'Welcome back.')
            return redirect('dashboard')
        else:
            error = 'Invalid email or password. Please try again.'
    return render(request, 'publisher/login.html', {'error': error, 'email': email})


def logout_view(request):
    logout(request)
    return redirect('login')


# ─── Dashboard ────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    context = {
        'total_posts': Post.objects.count(),
        'draft_posts': Post.objects.filter(status='draft').count(),
        'scheduled_posts': Post.objects.filter(status='scheduled').count(),
        'published_posts': Post.objects.filter(status='published').count(),
        'total_orgs': Organization.objects.count(),
        'total_accounts': SocialAccount.objects.count(),
        'total_staff': Staff.objects.count(),
        'recent_posts': Post.objects.select_related('organization', 'created_by').prefetch_related('images', 'platforms__social_account')[:5],
    }
    return render(request, 'publisher/dashboard.html', context)


# ─── Staff ────────────────────────────────────────────────────────────────────

@login_required
def staff_list(request):
    staff = Staff.objects.prefetch_related('role_assignments__role').all()
    return render(request, 'publisher/staff_list.html', {'staff': staff})


@login_required
def staff_create(request):
    form = StaffForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Staff member created.')
        return redirect('staff_list')
    return render(request, 'publisher/staff_create_edit.html', {'form': form, 'title': 'Add Staff Member', 'editing': False})


@login_required
def staff_edit(request, pk):
    obj = get_object_or_404(Staff, pk=pk)
    form = StaffForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Staff member updated.')
        return redirect('staff_list')
    return render(request, 'publisher/staff_create_edit.html', {'form': form, 'title': 'Edit Staff Member', 'editing': True})


@login_required
def staff_delete(request, pk):
    obj = get_object_or_404(Staff, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Staff member deleted.')
        return redirect('staff_list')
    return render(request, 'publisher/confirm_delete.html', {'obj': obj, 'title': 'Delete Staff Member', 'back_url': 'staff_list'})


# ─── Roles ────────────────────────────────────────────────────────────────────

@login_required
def role_list(request):
    roles = Role.objects.prefetch_related('permissions', 'staff_assignments').all()
    return render(request, 'publisher/role_list.html', {'roles': roles})


@login_required
def role_create(request):
    form = RoleForm(request.POST or None)
    perm_form = RolePermissionForm(request.POST or None)
    if form.is_valid() and perm_form.is_valid():
        role = form.save()
        perm = perm_form.save(commit=False)
        perm.role = role
        perm.save()
        messages.success(request, 'Role created.')
        return redirect('role_list')
    return render(request, 'publisher/role_form.html', {'form': form, 'perm_form': perm_form, 'title': 'Create Role'})


@login_required
def role_edit(request, pk):
    role = get_object_or_404(Role, pk=pk)
    perm, _ = RolePermission.objects.get_or_create(role=role)
    form = RoleForm(request.POST or None, instance=role)
    perm_form = RolePermissionForm(request.POST or None, instance=perm)
    if form.is_valid() and perm_form.is_valid():
        form.save()
        perm_form.save()
        messages.success(request, 'Role updated.')
        return redirect('role_list')
    return render(request, 'publisher/role_form.html', {'form': form, 'perm_form': perm_form, 'title': 'Edit Role'})


@login_required
def role_delete(request, pk):
    obj = get_object_or_404(Role, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Role deleted.')
        return redirect('role_list')
    return render(request, 'publisher/confirm_delete.html', {'obj': obj, 'title': 'Delete Role', 'back_url': 'role_list'})


# ─── Assignments ──────────────────────────────────────────────────────────────

@login_required
def assignment_list(request):
    assignments = StaffRoleAssignment.objects.select_related('staff', 'role').all()
    return render(request, 'publisher/assignment_list.html', {'assignments': assignments})


@login_required
def assignment_create(request):
    form = StaffRoleAssignmentForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Role assigned.')
        return redirect('assignment_list')
    return render(request, 'publisher/form.html', {'form': form, 'title': 'Assign Role to Staff', 'back_url': 'assignment_list'})


@login_required
def assignment_delete(request, pk):
    obj = get_object_or_404(StaffRoleAssignment, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Assignment removed.')
        return redirect('assignment_list')
    return render(request, 'publisher/confirm_delete.html', {'obj': obj, 'title': 'Remove Role Assignment', 'back_url': 'assignment_list'})


# ─── Organizations ────────────────────────────────────────────────────────────

@login_required
def org_list(request):
    orgs = Organization.objects.annotate(post_count=Count('posts'), account_count=Count('social_accounts'))
    return render(request, 'publisher/org_list.html', {'orgs': orgs})


@login_required
def org_create(request):
    form = OrganizationForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Organization created.')
        return redirect('org_list')
    return render(request, 'publisher/org_create_edit.html', {'form': form, 'title': 'Add Organization'})


@login_required
def org_edit(request, pk):
    obj = get_object_or_404(Organization, pk=pk)
    form = OrganizationForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Organization updated.')
        return redirect('org_list')
    return render(request, 'publisher/org_create_edit.html', {'form': form, 'title': 'Edit Organization', 'org': obj})


@login_required
def org_delete(request, pk):
    obj = get_object_or_404(Organization, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Organization deleted.')
        return redirect('org_list')
    return render(request, 'publisher/confirm_delete.html', {'obj': obj, 'title': 'Delete Organization', 'back_url': 'org_list'})


# ─── Social Accounts ──────────────────────────────────────────────────────────

@login_required
def account_list(request):
    accounts = SocialAccount.objects.select_related('organization').all()
    return render(request, 'publisher/account_list.html', {'accounts': accounts})


@login_required
def account_connect_choose(request):
    return render(request, 'publisher/account_connect_choose.html')


@login_required
def account_create(request):
    platform = request.GET.get('platform') or request.POST.get('platform', 'generic')
    from .forms import get_account_form, InstagramAccountForm, FacebookAccountForm
    FormClass = {'instagram': InstagramAccountForm, 'facebook': FacebookAccountForm}.get(platform)

    if FormClass:
        form = FormClass(request.POST or None)
    else:
        from .forms import GenericAccountForm
        form = GenericAccountForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        account = form.save(commit=False)
        account.platform = platform
        account.save()
        messages.success(request, f'{account.get_platform_display()} account connected successfully.')
        return redirect('account_list')

    return render(request, 'publisher/account_create_edit.html', {
        'form': form,
        'title': f'Connect {platform.title()} Account',
        'platform': platform,
    })


@login_required
def account_edit(request, pk):
    obj = get_object_or_404(SocialAccount, pk=pk)
    from .forms import get_account_form, InstagramAccountForm, FacebookAccountForm, GenericAccountForm
    FormClass = {'instagram': InstagramAccountForm, 'facebook': FacebookAccountForm}.get(obj.platform, GenericAccountForm)
    form = FormClass(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Social account updated.')
        return redirect('account_list')
    return render(request, 'publisher/account_create_edit.html', {
        'form': form,
        'title': f'Edit {obj.get_platform_display()} Account',
        'platform': obj.platform,
        'account': obj,
    })


@login_required
def account_delete(request, pk):
    obj = get_object_or_404(SocialAccount, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Social account disconnected.')
        return redirect('account_list')
    return render(request, 'publisher/confirm_delete.html', {'obj': obj, 'title': 'Disconnect Social Account', 'back_url': 'account_list'})


@login_required
def account_test(request, pk):
    """Test API connection for a social account — AJAX-friendly."""
    account = get_object_or_404(SocialAccount, pk=pk)
    from .publisher_engine import test_connection
    success, message, details = test_connection(account)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        from django.http import JsonResponse
        return JsonResponse({'success': success, 'message': message, 'details': details})
    if success:
        messages.success(request, f'Connection successful — {message}')
    else:
        messages.error(request, f'Connection failed — {message}')
    return redirect('account_list')


@login_required
def post_publish_now(request, pk):
    """Immediately publish a post to all pending platforms."""
    post = get_object_or_404(Post, pk=pk)
    if request.method != 'POST':
        return redirect('post_detail', pk=pk)

    # Validation — check Instagram posts have media
    for pp in post.platforms.filter(status='pending'):
        if pp.social_account.platform == 'instagram' and not post.images.exists():
            messages.error(request, 'Instagram requires at least one image. Add media before publishing.')
            return redirect('post_detail', pk=pk)

    from .publisher_engine import publish_post
    results = publish_post(post)

    for platform_name, success, msg in results:
        if success:
            messages.success(request, f'{platform_name}: {msg}')
        else:
            messages.error(request, f'{platform_name}: {msg}')

    if not results:
        messages.warning(request, 'No pending platforms to publish to.')

    return redirect('post_detail', pk=pk)


# ─── Posts ────────────────────────────────────────────────────────────────────

def _get_post_context(post=None):
    """Build context for post create/edit — social accounts + selected ids."""
    social_accounts = SocialAccount.objects.select_related('organization').order_by('platform', 'organization__name')
    selected_account_ids = set()
    if post:
        selected_account_ids = set(post.platforms.values_list('social_account_id', flat=True))
    return social_accounts, selected_account_ids


def _save_post_platforms(post, selected_ids):
    """Sync PostPlatform records to match the selected account ids."""
    existing = {pp.social_account_id: pp for pp in post.platforms.all()}
    new_ids = set(selected_ids)
    # Remove deselected
    for aid, pp in existing.items():
        if aid not in new_ids:
            pp.delete()
    # Add newly selected
    for aid in new_ids:
        if aid not in existing:
            try:
                account = SocialAccount.objects.get(pk=aid)
                PostPlatform.objects.create(post=post, social_account=account, status='pending')
            except SocialAccount.DoesNotExist:
                pass


def _save_post_media(request, post, replace=False):
    """
    Save images from the post form. Priority order:
      1. URL INPUT (image_url field) — always takes priority.
         Stored directly. Must be a public URL for Instagram.
      2. FILE UPLOAD (media_files) — only used if no URL was typed.
         Saved to /media/post_images/. Works locally for Facebook;
         needs deployment for Instagram (local URLs are not public).

    replace=True (edit mode) deletes the existing image at the same
    sort_order slot before inserting, preventing duplicates.
    """
    import os
    from django.core.files.storage import default_storage
    from django.core.files.base import ContentFile
    from django.conf import settings

    sort_order = int(request.POST.get('image_sort_order', 1))

    # ── Priority 1: URL field ─────────────────────────────────────────
    image_url = request.POST.get('image_url', '').strip()
    if image_url:
        if replace:
            post.images.filter(sort_order=sort_order).delete()
        ext = os.path.splitext(image_url.split('?')[0])[-1].lower()
        media_type = 'video' if ext in ('.mp4', '.mov', '.avi', '.webm') else 'image'
        PostImage.objects.create(
            post=post, image_url=image_url, sort_order=sort_order, media_type=media_type
        )
        return  # URL saved — skip file upload

    # ── Priority 2: file upload (no URL provided) ─────────────────────
    uploaded_files = request.FILES.getlist('media_files')
    for i, f in enumerate(uploaded_files):
        slot = sort_order + i
        if replace:
            post.images.filter(sort_order=slot).delete()
        ext = os.path.splitext(f.name)[1].lower()
        filename = f'post_images/post_{post.pk}_{slot}{ext}'
        saved_path = default_storage.save(filename, ContentFile(f.read()))
        media_url = request.build_absolute_uri(settings.MEDIA_URL + saved_path)
        media_type = 'video' if ext in ('.mp4', '.mov', '.avi', '.webm') else 'image'
        PostImage.objects.create(
            post=post, image_url=media_url, sort_order=slot, media_type=media_type
        )


@login_required
def post_list(request):
    posts = Post.objects.select_related('organization', 'created_by').prefetch_related('images', 'platforms__social_account')
    status_filter = request.GET.get('status')
    if status_filter:
        posts = posts.filter(status=status_filter)
    return render(request, 'publisher/post_list.html', {'posts': posts, 'status_filter': status_filter})


@login_required
def post_detail(request, pk):
    post = get_object_or_404(
        Post.objects.select_related('organization', 'created_by')
            .prefetch_related('images', 'platforms__social_account'),
        pk=pk
    )
    return render(request, 'publisher/post_detail.html', {'post': post})


@login_required
def post_create(request):
    form = PostForm(request.POST or None, request.FILES or None)
    social_accounts, selected_account_ids = _get_post_context()
    if request.method == 'POST' and form.is_valid():
        post = form.save()
        selected_ids = [int(x) for x in request.POST.getlist('platform_accounts')]
        _save_post_platforms(post, selected_ids)
        _save_post_media(request, post)
        messages.success(request, 'Post created.')
        return redirect('post_detail', pk=post.pk)
    return render(request, 'publisher/post_create_edit.html', {
        'form': form,
        'title': 'Create Post',
        'social_accounts': social_accounts,
        'selected_account_ids': selected_account_ids,
    })


@login_required
def post_edit(request, pk):
    obj = get_object_or_404(Post, pk=pk)
    form = PostForm(request.POST or None, request.FILES or None, instance=obj)
    social_accounts, selected_account_ids = _get_post_context(obj)
    if request.method == 'POST' and form.is_valid():
        post = form.save()
        selected_ids = [int(x) for x in request.POST.getlist('platform_accounts')]
        _save_post_platforms(post, selected_ids)
        _save_post_media(request, post, replace=True)
        # If status changed away from published, clear published_at and
        # reset all platform statuses back to pending so they re-publish.
        new_status = post.status
        if new_status != 'published':
            Post.objects.filter(pk=post.pk).update(published_at=None)
            post.platforms.all().update(status='pending')
        messages.success(request, 'Post updated.')
        return redirect('post_detail', pk=post.pk)
    return render(request, 'publisher/post_create_edit.html', {
        'form': form,
        'title': 'Edit Post',
        'post': obj,
        'social_accounts': social_accounts,
        'selected_account_ids': selected_account_ids,
    })


@login_required
def post_delete(request, pk):
    obj = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Post deleted.')
        return redirect('post_list')
    return render(request, 'publisher/confirm_delete.html', {'obj': obj, 'title': 'Delete Post', 'back_url': 'post_list'})


# ─── Post Platforms ───────────────────────────────────────────────────────────

@login_required
def post_platform_create(request):
    form = PostPlatformForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Platform added.')
        return redirect('post_list')
    return render(request, 'publisher/form.html', {'form': form, 'title': 'Add Platform to Post', 'back_url': 'post_list'})


@login_required
def post_platform_edit(request, pk):
    obj = get_object_or_404(PostPlatform, pk=pk)
    form = PostPlatformForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Platform updated.')
        return redirect('post_detail', pk=obj.post_id)
    return render(request, 'publisher/form.html', {'form': form, 'title': 'Edit Platform Status', 'back_url': 'post_list'})


@login_required
def post_platform_delete(request, pk):
    obj = get_object_or_404(PostPlatform, pk=pk)
    post_id = obj.post_id
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Platform removed.')
        return redirect('post_detail', pk=post_id)
    return render(request, 'publisher/confirm_delete.html', {'obj': obj, 'title': 'Remove Platform', 'back_url': 'post_list'})


# ─── Post Images ──────────────────────────────────────────────────────────────

@login_required
def post_image_delete(request, pk):
    """Delete a PostImage — AJAX (returns JSON) or normal POST."""
    obj = get_object_or_404(PostImage, pk=pk)
    post_id = obj.post_id
    if request.method == 'POST':
        obj.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            from django.http import JsonResponse
            return JsonResponse({'success': True})
        messages.success(request, 'Image removed.')
        return redirect('post_detail', pk=post_id)
    return render(request, 'publisher/confirm_delete.html', {
        'obj': obj, 'title': 'Remove Image', 'back_url': 'post_list'
    })


@login_required
def post_analytics(request, pk):
    """Fetch and display analytics for a published post."""
    post = get_object_or_404(
        Post.objects.select_related('organization', 'created_by')
            .prefetch_related('platforms__social_account'),
        pk=pk
    )
    analytics = []
    if post.status == 'published':
        from .publisher_engine import fetch_post_analytics
        analytics = fetch_post_analytics(post)
    return render(request, 'publisher/post_analytics.html', {
        'post': post,
        'analytics': analytics,
    })


# ─── Meta Webhooks ────────────────────────────────────────────────────────────

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
import json as _json

@csrf_exempt
def webhook_meta(request):
    """
    Single endpoint for all Meta (Instagram / Facebook) webhooks.

    GET  — Verification handshake.
           Meta sends hub.mode, hub.verify_token, hub.challenge.
           We confirm the verify token matches and echo back hub.challenge.
           Callback URL to enter in Meta Dashboard:
               https://your-domain.com/webhooks/meta/
           Verify Token (enter the same string in Meta Dashboard):
               value of WEBHOOK_VERIFY_TOKEN in your .env

    POST — Event notification.
           Meta sends a JSON payload describing the event.
           We store it in WebhookEvent and can act on it.
    """
    from django.conf import settings
    from .models import WebhookEvent

    # ── GET: Verification handshake ───────────────────────────────────
    if request.method == 'GET':
        mode      = request.GET.get('hub.mode', '')
        token     = request.GET.get('hub.verify_token', '')
        challenge = request.GET.get('hub.challenge', '')

        expected_token = getattr(settings, 'WEBHOOK_VERIFY_TOKEN', '')

        if mode == 'subscribe' and token == expected_token:
            # Respond with the challenge to confirm ownership
            return HttpResponse(challenge, content_type='text/plain', status=200)
        else:
            # Token mismatch — reject
            return HttpResponse('Forbidden', status=403)

    # ── POST: Incoming event ──────────────────────────────────────────
    if request.method == 'POST':
        try:
            payload = _json.loads(request.body)
        except _json.JSONDecodeError:
            return HttpResponse('Bad Request', status=400)

        # Parse top-level fields
        object_type = payload.get('object', '')   # 'instagram' or 'page'
        platform = 'facebook' if object_type == 'page' else 'instagram'
        entries = payload.get('entry', [])

        for entry in entries:
            entry_id = str(entry.get('id', ''))
            changes = entry.get('changes', [])
            messaging = entry.get('messaging', [])

            # Handle field-based changes (comments, mentions, etc.)
            for change in changes:
                field = change.get('field', '')
                WebhookEvent.objects.create(
                    platform=platform,
                    object_type=object_type,
                    entry_id=entry_id,
                    field=field,
                    raw_payload=_json.dumps(payload),
                )

            # Handle messaging events
            for msg in messaging:
                WebhookEvent.objects.create(
                    platform=platform,
                    object_type=object_type,
                    entry_id=entry_id,
                    field='messages',
                    raw_payload=_json.dumps(payload),
                )

            # If no changes or messaging, store the raw entry anyway
            if not changes and not messaging:
                WebhookEvent.objects.create(
                    platform=platform,
                    object_type=object_type,
                    entry_id=entry_id,
                    field='unknown',
                    raw_payload=_json.dumps(payload),
                )

        return JsonResponse({'status': 'ok'}, status=200)

    return HttpResponse('Method Not Allowed', status=405)


@login_required
def webhook_events(request):
    """View incoming webhook events stored from Meta."""
    from .models import WebhookEvent
    events = WebhookEvent.objects.all()[:100]
    return render(request, 'publisher/webhook_events.html', {'events': events})
