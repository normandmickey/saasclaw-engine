import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import GitHubInstallation


@login_required
def github_setup(request):
    installations = GitHubInstallation.objects.order_by('account_name', 'installation_id')
    return render(request, 'app/github_setup.html', {
        'installations': installations,
        'github_app_id': settings.GITHUB_APP_ID,
        'github_app_configured': bool(settings.GITHUB_APP_ID and (settings.GITHUB_APP_PRIVATE_KEY or settings.GITHUB_APP_PRIVATE_KEY_PATH) and settings.GITHUB_WEBHOOK_SECRET),
    })


@csrf_exempt
@require_POST
def github_webhook(request):
    event = request.headers.get('X-GitHub-Event', '').strip()
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON payload.')

    if not settings.GITHUB_WEBHOOK_SECRET:
        return HttpResponseBadRequest('GitHub webhook secret is not configured.')

    if event == 'installation':
        installation = payload.get('installation') or {}
        account = installation.get('account') or {}
        installation_id = installation.get('id')
        if installation_id:
            GitHubInstallation.objects.update_or_create(
                installation_id=installation_id,
                defaults={
                    'account_name': account.get('login') or f'installation-{installation_id}',
                    'account_type': account.get('type') or '',
                    'github_account_id': account.get('id'),
                    'access_metadata_json': payload,
                },
            )

    return JsonResponse({'ok': True, 'event': event})
