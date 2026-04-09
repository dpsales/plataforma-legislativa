from __future__ import annotations

from django.contrib import messages
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import ConfigurationForm, UploadRequerimentosForm
from .importador import ImportadorRequerimentos
from .models import Configuration, Requerimento

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
    
    # Busca os requerimentos armazenados
    requerimentos = Requerimento.objects.all()
    
    # Filtra por configuração se houver (opcional)
    if config.presentation_years:
        anos = config.presentation_years
        requerimentos = requerimentos.filter(data_apresentacao__year__in=anos)
    
    configure_url = ""
    if can_configure:
        configure_url = _append_profile(
            _prefixed_path(request, reverse("requisicoes:configure")),
            profile,
        )

    upload_form = UploadRequerimentosForm()

    context = {
        "profile": profile,
        "can_configure": can_configure,
        "configure_url": configure_url,
        "config": config,
        "unit_groups": config.unit_groups or [],
        "config_updated_at": timezone.localtime(config.updated_at) if config.updated_at else None,
        "requerimentos": requerimentos,
        "total_requerimentos": requerimentos.count(),
        "upload_form": upload_form,
    }
    return render(request, "requisicoes/index.html", context)


def upload_requerimentos(request: HttpRequest) -> HttpResponse:
    profile = _request_profile(request)
    if profile not in ALLOWED_CONFIG_PROFILES:
        messages.error(
            request,
            "Somente usuários com perfil administrador ou normal podem importar arquivos.",
        )
        index_url = _append_profile(
            _prefixed_path(request, reverse("requisicoes:index")),
            profile,
        )
        return redirect(index_url)

    if request.method != "POST":
        return redirect(_append_profile(_prefixed_path(request, reverse("requisicoes:index")), profile))

    form = UploadRequerimentosForm(request.POST, request.FILES)
    if not form.is_valid():
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
        return redirect(_append_profile(_prefixed_path(request, reverse("requisicoes:index")), profile))

    arquivo = form.cleaned_data["arquivo"]
    delimiter = form.cleaned_data.get("delimiter") or ";"
    sheet = form.cleaned_data.get("sheet") or None
    clear_before = form.cleaned_data.get("clear_before", False)

    if clear_before:
        Requerimento.objects.all().delete()

    try:
        criados, atualizados, erros = ImportadorRequerimentos.from_file(
            arquivo,
            arquivo.name,
            delimiter=delimiter,
            sheet=sheet,
        )
        messages.success(
            request,
            f"Importação concluída: {criados + atualizados} registros processados, {erros} erros.",
        )
    except Exception as exc:
        messages.error(request, f"Erro ao importar arquivo: {exc}")

    return redirect(_append_profile(_prefixed_path(request, reverse("requisicoes:index")), profile))


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
