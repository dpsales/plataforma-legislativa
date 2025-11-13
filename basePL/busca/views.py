from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def _request_profile(request: HttpRequest) -> str:
    for source in (request.GET, request.POST):
        profile = source.get("profile")
        if profile:
            return profile.strip().lower()
    header = request.META.get("HTTP_X_USER_PROFILE")
    if header:
        return header.strip().lower()
    return ""


def _prefixed_path(request: HttpRequest, path: str) -> str:
    prefix = request.META.get("HTTP_X_FORWARDED_PREFIX") or request.META.get("SCRIPT_NAME") or ""
    prefix = prefix.rstrip("/")
    if path.startswith("http://") or path.startswith("https://"):
        return path
    relative = path.lstrip("/")
    if prefix:
        base = prefix or "/"
        return f"{base}/{relative}" if relative else base
    return f"/{relative}" if relative else "/"


def index(request: HttpRequest) -> HttpResponse:
    profile = _request_profile(request)
    
    context = {
        "profile": profile,
        "static_prefix": _prefixed_path(request, "static").rstrip("/"),
    }
    return render(request, "busca/index.html", context)

