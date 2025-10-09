from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from accounts.models import Module, Role, RoleModulePermission

# =========================
#   CONFIG ECOENERGY
# =========================
ROLES = [
    "Cliente - Admin",
    "Cliente - Electrónico",
    "EcoEnergy - Admin",
]

MODULES = [
    ("operacion",    "Operación"),     # devices, measurements, alerts, zones
    ("catalogo",     "Catálogo"),      # products, categories, alert rules
    ("organizacion", "Organización"),  # organizations, user profiles
]

MATRIX = {
    "Cliente - Admin": {
        "operacion": "all",
        "catalogo": "all",
        "organizacion": "all",
    },
    "Cliente - Electrónico": {
        "operacion": ("view",),  # puedes sumar add_measurement en EXTRA_NATIVE_PERMS
    },
    "EcoEnergy - Admin": {
        "catalogo": "all",
        "organizacion": "all",
        # "operacion": "all",  # si quieres que también vea operación global, actívalo
    },
}

SYNC_NATIVE_DJANGO_PERMS = True

# mapea módulos a app_label y modelos reales
APP_MODEL_MAP = {
    "operacion": {
        "app_label": "dispositivos",
        "models": ["device", "measurement", "alertevent", "zone"],
    },
    "catalogo": {
        "app_label": "dispositivos",
        "models": ["product", "category", "alertrule", "productalertrule"],
    },
    "organizacion": {
        "app_label": "organizations",
        "models": ["organization", "userprofile"],
    },
}

# Permisos nativos extra por rol: (app_label, codename)
EXTRA_NATIVE_PERMS = {
    "Cliente - Electrónico": [
        ("dispositivos", "add_measurement"),
        # ("dispositivos", "change_measurement"),
    ],
}

def _as_tuple(actions):
    if actions == "all":
        return {"view", "add", "change", "delete"}
    return set(actions)

def _model_perms(app_label, model, actions=("view", "add", "change", "delete")):
    try:
        ct = ContentType.objects.get(app_label=app_label, model=model)
    except ContentType.DoesNotExist:
        return Permission.objects.none()
    codenames = [f"{act}_{model}" for act in actions]
    return Permission.objects.filter(content_type=ct, codename__in=codenames)

def _sync_native_perms_for_role(group: Group, module_code: str, actions):
    if module_code not in APP_MODEL_MAP:
        return
    acts = _as_tuple(actions)
    app_label = APP_MODEL_MAP[module_code]["app_label"]
    models = APP_MODEL_MAP[module_code]["models"]

    perms = Permission.objects.none()
    for m in models:
        perms |= _model_perms(app_label, m, actions=acts)

    if perms.exists():
        group.permissions.add(*perms)

def _apply_extra_perms(group: Group, pairs):
    for app_label, codename in pairs:
        try:
            p = Permission.objects.get(content_type__app_label=app_label, codename=codename)
            group.permissions.add(p)
        except Permission.DoesNotExist:
            continue

class Command(BaseCommand):
    help = "Siembra roles/módulos/matriz para EcoEnergy y sincroniza permisos nativos para Admin."

    @transaction.atomic
    def handle(self, *args, **options):
        # 1) Módulos
        modules = {}
        for code, name in MODULES:
            m, _ = Module.objects.get_or_create(code=code, defaults={"name": name})
            if m.name != name:
                m.name = name
                m.save(update_fields=["name"])
            modules[code] = m

        # 2) Roles (Group + Role 1:1)
        groups_roles = {}
        for rname in ROLES:
            g, _ = Group.objects.get_or_create(name=rname)
            role, _ = Role.objects.get_or_create(group=g)
            groups_roles[rname] = (g, role)

        # 3) Matriz + permisos nativos
        for rname, modmap in MATRIX.items():
            if rname not in groups_roles:
                continue
            group, role = groups_roles[rname]

            if SYNC_NATIVE_DJANGO_PERMS:
                group.permissions.clear()

            for mcode, actions in modmap.items():
                if mcode not in modules:
                    continue

                acts = _as_tuple(actions)
                RoleModulePermission.objects.update_or_create(
                    role=role, module=modules[mcode],
                    defaults={
                        "can_view":   "view" in acts,
                        "can_add":    "add" in acts,
                        "can_change": "change" in acts,
                        "can_delete": "delete" in acts,
                    }
                )
                if SYNC_NATIVE_DJANGO_PERMS:
                    _sync_native_perms_for_role(group, mcode, actions)

            if SYNC_NATIVE_DJANGO_PERMS and rname in EXTRA_NATIVE_PERMS:
                _apply_extra_perms(group, EXTRA_NATIVE_PERMS[rname])

        self.stdout.write(self.style.SUCCESS("EcoEnergy: roles, módulos y matriz listos"))
        if SYNC_NATIVE_DJANGO_PERMS:
            self.stdout.write(self.style.SUCCESS("Permisos nativos sincronizados para el Admin"))
