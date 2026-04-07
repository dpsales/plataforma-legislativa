from __future__ import annotations

from typing import Dict, List
from urllib.parse import quote

from django.conf import settings
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .forms import LoginForm


def _is_authenticated(request) -> bool:
    return bool(request.session.get("authenticated"))


def _get_next_url(request) -> str:
    next_url = request.GET.get("next") or request.POST.get("next")
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    return reverse("portal:home")


def _filtered_paginas(user_profile: str) -> List[Dict[str, str]]:
    def _build_page(page_config: Dict[str, str]) -> Dict[str, str]:
        page = {k: v for k, v in page_config.items() if k != "roles"}
        if page.get("url", "").startswith("/redirect/"):
            slug = page["url"].split("/redirect/")[-1]
            page["url"] = reverse("portal:redirect", args=[slug])
        return page

    profile = user_profile if user_profile in settings.PROFILE_RULES else settings.DEFAULT_PROFILE
    paginas: List[Dict[str, str]] = []
    for page in settings.PAGINAS:
        roles = page.get("roles")
        if roles and profile not in roles:
            continue
        paginas.append(_build_page(page))
    return paginas


@require_http_methods(["GET", "POST"])
def login_view(request):
    if _is_authenticated(request):
        return redirect("portal:home")

    form = LoginForm(request.POST or None)
    next_param = request.GET.get("next") or request.POST.get("next") or ""
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"].lower()
        token = form.cleaned_data["token"]
        user = settings.VALID_USERS.get(email)

        if user and user.get("token") == token:
            profile = user.get("profile", settings.DEFAULT_PROFILE)
            if profile not in settings.PROFILE_RULES:
                profile = settings.DEFAULT_PROFILE
            request.session["authenticated"] = True
            request.session["email"] = email
            request.session["profile"] = profile
            return redirect(_get_next_url(request))

        form.add_error(None, "Email ou token inválidos.")

    return render(request, "login.html", {"form": form, "next": next_param})


def logout_view(request):
    request.session.flush()
    return redirect("portal:login")


def _login_redirect(request):
    next_param = quote(request.get_full_path())
    return redirect(f"{reverse('portal:login')}?next={next_param}")


def portal_home(request):
    if not _is_authenticated(request):
        return _login_redirect(request)

    profile = request.session.get("profile", settings.DEFAULT_PROFILE)
    rules = settings.PROFILE_RULES.get(profile, settings.PROFILE_RULES[settings.DEFAULT_PROFILE])
    paginas = _filtered_paginas(profile)
    context = {
        "paginas": paginas,
        "user_email": request.session.get("email"),
        "user_profile": profile,
        "profile_label": rules["label"],
        "can_configure": rules["can_configure"],
    }
    return render(request, "portal_index.html", context)


def manual_view(request):
    if not _is_authenticated(request):
        return _login_redirect(request)

    manual_conteudo = (
        """
        <p>Aqui você encontrará informações essenciais para utilizar a Plataforma do Congresso</p>
        <ul>
            <li><strong>Navegação:</strong> Utilize o menu superior para acessar a página inicial, o manual e a documentação.</li>
            <li><strong>Informativo do Congresso:</strong> Link para o site de acompanhamento das proposições e votações.</li>
            <li><strong>Agenda da Semana:</strong> Veja os eventos e proposições previstos para a semana.</li>
            <li><strong>Requerimentos:</strong> Consulte os requerimentos apresentados na Câmara e no Senado.</li>
            <li><strong>Matérias em Tramitação (Senado):</strong> Consulte as matérias prontas para pauta.</li>
            <li><strong>Matérias em Tramitação (Câmara):</strong> Consulte as matérias prontas para pauta.</li>
            <li><strong>Matérias Prioritárias:</strong> Consulte o status das matérias de interesse.</li>
            <li><strong>Busca Avançada em Proposições:</strong> Base de matérias em tramitação na Câmara.</li>
        </ul>
        """
    )
    return render(request, "manual.html", {"manual_conteudo": manual_conteudo})


def documentation_view(request):
    if not _is_authenticated(request):
        return _login_redirect(request)

    doc_conteudo = (
        """
        <h2>Documentação do Sistema</h2>
        <p>Aqui você encontrará a documentação técnica e funcional da Plataforma Legislativa.</p>
        <h3>Principais Endpoints</h3>
        <ul>
            <li><strong>/</strong>: Página inicial com links para as aplicações.</li>
            <li><strong>/manual</strong>: Manual do Usuário.</li>
            <li><strong>/documentacao</strong>: Documentação técnica do sistema.</li>
        </ul>
        <h3>Atualizações e Versionamento</h3>
        """
    )
    return render(request, "documentacao.html", {"doc_conteudo": doc_conteudo})


@require_http_methods(["GET"])
def configuration_view(request):
    if not _is_authenticated(request):
        return _login_redirect(request)

    profile = request.session.get("profile", settings.DEFAULT_PROFILE)
    rules = settings.PROFILE_RULES.get(profile, settings.PROFILE_RULES[settings.DEFAULT_PROFILE])
    if not rules["can_configure"]:
        return redirect("portal:home")

    context = {
        "profile_label": rules["label"],
        "user_email": request.session.get("email"),
        "user_profile": profile,
        "can_configure": True,
    }
    return render(request, "configuracao.html", context)


def redirect_view(request, page_name: str):
    if not _is_authenticated(request):
        return _login_redirect(request)

    url = settings.REDIRECT_URLS.get(page_name, reverse("portal:home"))
    return redirect(url)
