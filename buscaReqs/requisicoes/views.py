from __future__ import annotations

from django.contrib import messages
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import ConfigurationForm
from .models import Configuration

ALLOWED_CONFIG_PROFILES = {"admin", "normal"}


def _request_profile(request: HttpRequest) -> str:
    for source in (request.GET, request.POST):
        profile = source.get("profile")
        if profile:
            return profile.strip().lower()
    header = request.META.get("HTTP_X_USER_PROFILE", "").strip().lower()
    return header


def _prefixed_path(request: HttpRequest, path: str) -> str:
    prefix = request.META.get("HTTP_X_FORWARDED_PREFIX") or request.META.get("SCRIPT_NAME") or ""
    prefix = prefix.rstrip("/")
    if path.startswith("http://") or path.startswith("https://"):
        return path
    relative = path.lstrip("/")
    if prefix:
        return f"{prefix}/{relative}" if relative else prefix or "/"
    return f"/{relative}" if relative else "/"


def _append_profile(path: str, profile: str) -> str:
    if not profile:
        return path
    separator = "&" if "?" in path else "?"
    return f"{path}{separator}profile={profile}"


def homepage(request: HttpRequest) -> HttpResponse:
    profile = _request_profile(request)
    can_configure = profile in ALLOWED_CONFIG_PROFILES
    config = Configuration.load()
    configure_url = ""
    if can_configure:
        configure_url = _append_profile(
            _prefixed_path(request, reverse("requisicoes:configure")),
            profile,
        )

    context = {
        "profile": profile,
        "can_configure": can_configure,
        "configure_url": configure_url,
        "config": config,
        "unit_groups": config.unit_groups or [],
        "config_updated_at": timezone.localtime(config.updated_at) if config.updated_at else None,
    }
    return render(request, "requisicoes/index.html", context)


def configure(request: HttpRequest) -> HttpResponse:
    profile = _request_profile(request)
    if profile not in ALLOWED_CONFIG_PROFILES:
        messages.error(
            request,
            "Somente usuários com perfil administrador ou normal podem alterar estas configurações.",
        )
        index_url = _append_profile(
            _prefixed_path(request, reverse("requisicoes:index")),
            profile,
        )
        return redirect(index_url)

    configuration = Configuration.load()

    if request.method == "POST":
        form = ConfigurationForm(request.POST, config=configuration)
        if form.is_valid():
            form.save()
            messages.success(request, "Configurações atualizadas com sucesso.")
            url = _append_profile(
                _prefixed_path(request, reverse("requisicoes:configure")),
                profile,
            )
            return redirect(url)
    else:
        form = ConfigurationForm(config=configuration)

    context = {
        "form": form,
        "profile": profile,
        "index_url": _append_profile(
            _prefixed_path(request, reverse("requisicoes:index")),
            profile,
        ),
        "updated_at": timezone.localtime(configuration.updated_at) if configuration.updated_at else None,
        "unit_groups": configuration.unit_groups or [],
    }
    return render(request, "requisicoes/configure.html", context)


def configuration_detail(_: HttpRequest) -> JsonResponse:
    configuration = Configuration.load()
    return JsonResponse(
        {
            "name": configuration.name,
            "updated_at": (
                timezone.localtime(configuration.updated_at).isoformat()
                if configuration.updated_at
                else None
            ),
            "proposition_types": configuration.proposition_types or [],
            "presentation_years": configuration.presentation_years or [],
            "unit_groups": configuration.unit_groups or [],
            "subjects": configuration.subjects or [],
        }
    )
