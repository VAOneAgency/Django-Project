"""
OnePulse Social Publisher — Publishing Engine
Handles actual API calls to Instagram and Facebook Graph API.
"""
import json
import logging
import urllib.request
import urllib.parse
import urllib.error
from django.utils import timezone

logger = logging.getLogger(__name__)

GRAPH_API_VERSION = "v25.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


# ─── Low-level HTTP helpers ───────────────────────────────────────────────────

def _graph_get(path, params):
    """GET request to Graph API. Returns (data_dict, error_str)."""
    qs = urllib.parse.urlencode(params)
    url = f"{GRAPH_BASE}/{path.lstrip('/')}?{qs}"
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            return json.loads(resp.read()), None
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        try:
            err = json.loads(body).get('error', {})
            msg = err.get('message', body)
        except Exception:
            msg = body
        logger.error("Graph GET %s → %s", path, msg)
        return None, msg
    except Exception as e:
        return None, str(e)


def _graph_post(path, params, data=None):
    """POST request to Graph API. Returns (data_dict, error_str)."""
    url = f"{GRAPH_BASE}/{path.lstrip('/')}"
    payload = dict(params)
    if data:
        payload.update(data)
    encoded = urllib.parse.urlencode(payload).encode('utf-8')
    req = urllib.request.Request(url, data=encoded, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read()), None
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        try:
            err = json.loads(body).get('error', {})
            msg = f"[{err.get('code','?')}] {err.get('message', body)}"
        except Exception:
            msg = body
        logger.error("Graph POST %s → %s", path, msg)
        return None, msg
    except Exception as e:
        return None, str(e)


# ─── Connection Test ──────────────────────────────────────────────────────────

def test_instagram_connection(account):
    """
    Test that the Instagram account credentials are valid.
    Returns (success: bool, message: str, details: dict).
    """
    if not account.ig_business_account_id or not account.access_token:
        return False, "Missing IG Business Account ID or access token.", {}

    ig_id = account.ig_business_account_id
    data, err = _graph_get(ig_id, {
        'fields': 'id,username,profile_picture_url,followers_count,media_count',
        'access_token': account.access_token,
    })
    if err:
        return False, f"Instagram API error: {err}", {}

    # Valid if Meta returns id and username — account_type field is not needed
    if not data.get('id') or not data.get('username'):
        return False, f"Unexpected response from Instagram API: {data}", {}

    followers = data.get('followers_count', '?')
    media = data.get('media_count', '?')
    return True, f"Connected as @{data.get('username')} — {followers} followers, {media} posts", data


def test_facebook_connection(account):
    """
    Test Facebook Page token validity.
    Returns (success: bool, message: str, details: dict).
    """
    if not account.page_id or not account.access_token:
        return False, "Missing Page ID or access token.", {}

    data, err = _graph_get(account.page_id, {
        'fields': 'id,name,fan_count,link',
        'access_token': account.access_token,
    })
    if err:
        return False, f"Facebook API error: {err}", {}

    return True, f"Connected to Page: {data.get('name','?')} ({data.get('fan_count','?')} fans)", data


def test_connection(account):
    """Dispatch to the right test based on platform."""
    if account.platform == 'instagram':
        return test_instagram_connection(account)
    elif account.platform == 'facebook':
        return test_facebook_connection(account)
    else:
        return False, f"Connection testing not yet implemented for {account.get_platform_display()}.", {}


# ─── Instagram Publishing ─────────────────────────────────────────────────────

def publish_to_instagram(post, platform_record, account):
    """
    Publish a post to Instagram using the Content Publishing API.
    Two-step: create media container → publish container.
    Returns (success: bool, message: str, published_id: str).

    Docs: https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/content-publishing
    """
    ig_id = account.ig_business_account_id
    token = account.access_token

    if not ig_id:
        return False, "No Instagram Business Account ID set on this account.", ""
    if not token:
        return False, "No access token set on this account.", ""

    # Get first image attached to the post
    image = post.images.first()
    if not image:
        return False, "Instagram requires at least one image. No media attached to this post.", ""

    image_url = image.image_url
    caption = post.caption or ""
    is_video = image.media_type == 'video'

    # ── Validate URL is publicly accessible ──
    # Instagram cannot fetch local/private URLs like 127.0.0.1 or localhost
    local_indicators = ('127.0.0.1', 'localhost', '0.0.0.0', '::1')
    if any(x in image_url for x in local_indicators):
        return False, (
            "Image URL is not publicly accessible. Instagram requires a public URL. "
            "Deploy to Heroku or use a public image hosting service (Cloudinary, imgbb, "
            "S3) and paste the public URL in the 'Add by URL' field instead of uploading directly."
        ), ""

    # ── Step 1: Create media container ──
    container_params = {'access_token': token}
    if is_video:
        container_params.update({'media_type': 'REELS', 'video_url': image_url, 'caption': caption})
    else:
        container_params.update({'image_url': image_url, 'caption': caption})

    container_data, err = _graph_post(f"{ig_id}/media", container_params)
    if err:
        return False, f"Failed to create IG media container: {err}", ""

    container_id = container_data.get('id')
    if not container_id:
        return False, f"No container ID returned: {container_data}", ""

    # ── Step 2: Publish the container ──
    publish_data, err = _graph_post(f"{ig_id}/media_publish", {
        'creation_id': container_id,
        'access_token': token,
    })
    if err:
        return False, f"Failed to publish IG container: {err}", ""

    published_id = publish_data.get('id', '')
    return True, f"Published to Instagram. Post ID: {published_id}", published_id


# ─── Facebook Publishing ──────────────────────────────────────────────────────

def publish_to_facebook(post, platform_record, account):
    """
    Publish a post to a Facebook Page.
    POST /{page-id}/feed with message + optional picture.
    Returns (success: bool, message: str, published_id: str).
    """
    page_id = account.page_id
    token = account.access_token

    if not page_id:
        return False, "No Facebook Page ID set on this account.", ""
    if not token:
        return False, "No access token set on this account.", ""

    params = {
        'message': post.caption or "",
        'access_token': token,
    }

    # Attach first image if available
    image = post.images.first()
    if image and image.media_type == 'image':
        params['picture'] = image.image_url

    feed_data, err = _graph_post(f"{page_id}/feed", params)
    if err:
        return False, f"Failed to post to Facebook Page: {err}", ""

    published_id = feed_data.get('id', '')
    return True, f"Published to Facebook Page. Post ID: {published_id}", published_id


# ─── Main Dispatch ────────────────────────────────────────────────────────────

def publish_platform(post, platform_record):
    """
    Publish a single PostPlatform record.
    Updates the PostPlatform status, error_message, published_post_id.
    Returns (success: bool, message: str).
    """
    from .models import PostPlatform
    account = platform_record.social_account

    platform = account.platform
    try:
        if platform == 'instagram':
            success, message, pub_id = publish_to_instagram(post, platform_record, account)
        elif platform == 'facebook':
            success, message, pub_id = publish_to_facebook(post, platform_record, account)
        else:
            success, message, pub_id = False, f"Publishing not implemented for {account.get_platform_display()}", ""
    except Exception as e:
        success, message, pub_id = False, f"Unexpected error: {e}", ""
        logger.exception("Unhandled error publishing post %s to %s", post.pk, platform)

    # Update the PostPlatform record
    platform_record.status = 'published' if success else 'failed'
    platform_record.error_message = None if success else message
    if pub_id:
        platform_record.published_post_id = pub_id
    platform_record.save(update_fields=['status', 'error_message', 'published_post_id'])

    # Update the SocialAccount last_used_at
    if success:
        account.last_used_at = timezone.now()
        account.save(update_fields=['last_used_at'])

    return success, message


def publish_post(post):
    """
    Attempt to publish a Post to all its pending platforms.
    Returns list of (platform_display, success, message).
    """
    from django.utils import timezone
    results = []
    pending = post.platforms.filter(status='pending').select_related('social_account__organization')

    for pp in pending:
        success, msg = publish_platform(post, pp)
        results.append((pp.social_account.get_platform_display(), success, msg))

    # Update top-level post status
    all_pp = post.platforms.all()
    if all_pp.filter(status='published').count() == all_pp.count() and all_pp.count() > 0:
        post.status = 'published'
        post.published_at = timezone.now()
        post.save(update_fields=['status', 'published_at'])
    elif all_pp.filter(status='failed').count() > 0:
        post.status = 'failed'
        post.save(update_fields=['status'])

    return results


# ─── Analytics ────────────────────────────────────────────────────────────────

def fetch_instagram_insights(platform_record):
    """
    Fetch reach, impressions, and follower/non-follower breakdown
    for a published Instagram post.

    Requires: platform_record.published_post_id
    Endpoint: GET /{media-id}/insights
    Metrics: reach, impressions, follows, profile_visits,
             ig_reels_aggregated_all_plays_count (for reels)

    Returns (data: dict, error: str|None)
    """
    account = platform_record.social_account
    media_id = platform_record.published_post_id
    token = account.access_token

    if not media_id:
        return None, "No published post ID recorded — post may not have been published via OnePulse."
    if not token:
        return None, "No access token on this account."

    # First get basic media info
    media_data, err = _graph_get(media_id, {
        'fields': 'id,media_type,timestamp,like_count,comments_count,thumbnail_url,media_url',
        'access_token': token,
    })
    if err:
        return None, f"Could not fetch media info: {err}"

    # Then get insights
    insights_data, err = _graph_get(f"{media_id}/insights", {
        'metric': 'reach,impressions,follows,profile_visits,saved',
        'access_token': token,
    })

    result = {'media': media_data, 'insights': {}, 'breakdown': None}

    if err:
        result['insights_error'] = err
    else:
        for item in insights_data.get('data', []):
            result['insights'][item['name']] = item.get('values', [{}])[0].get('value', item.get('value', 0))

    # Follower vs non-follower breakdown via reach breakdown
    breakdown_data, berr = _graph_get(f"{media_id}/insights", {
        'metric': 'reach',
        'breakdown': 'follow_type',
        'access_token': token,
    })
    if not berr and breakdown_data.get('data'):
        try:
            breakdown_vals = breakdown_data['data'][0].get('total_value', {}).get('breakdowns', [])
            if breakdown_vals:
                result['breakdown'] = breakdown_vals[0].get('results', [])
        except (IndexError, KeyError):
            pass

    return result, None


def fetch_facebook_insights(platform_record):
    """
    Fetch reach and engagement for a published Facebook post.
    Endpoint: GET /{post-id}/insights
    Returns (data: dict, error: str|None)
    """
    account = platform_record.social_account
    post_id = platform_record.published_post_id
    token = account.access_token

    if not post_id:
        return None, "No published post ID recorded."
    if not token:
        return None, "No access token on this account."

    insights_data, err = _graph_get(f"{post_id}/insights", {
        'metric': 'post_impressions,post_impressions_unique,post_engaged_users,post_clicks',
        'access_token': token,
    })
    if err:
        return None, f"Facebook Insights error: {err}"

    result = {'insights': {}}
    for item in insights_data.get('data', []):
        result['insights'][item['name']] = item.get('values', [{}])[-1].get('value', 0)

    return result, None


def fetch_post_analytics(post):
    """
    Aggregate analytics for all published platforms on a post.
    Returns list of {platform, account_name, data, error}
    """
    results = []
    for pp in post.platforms.filter(status='published').select_related('social_account__organization'):
        platform = pp.social_account.platform
        if platform == 'instagram':
            data, err = fetch_instagram_insights(pp)
        elif platform == 'facebook':
            data, err = fetch_facebook_insights(pp)
        else:
            data, err = None, f"Analytics not yet available for {pp.social_account.get_platform_display()}"
        results.append({
            'platform': platform,
            'platform_display': pp.social_account.get_platform_display(),
            'account_name': pp.social_account.account_name or pp.social_account.account_id,
            'published_post_id': pp.published_post_id,
            'data': data,
            'error': err,
        })
    return results
