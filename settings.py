#
# This file is part of the BIOM_AID distribution (https://bitbucket.org/kig13/dem/).
# Copyright (c) 2020-2021 Brice Nord, Romuald Kliglich, Alexandre Jaborska, Philomène Mazand.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
import configparser
import logging
import os

from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from tomlkit.toml_file import TOMLFile

from settings import INSTALLED_APPS

import dem
import common

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logging.getLogger(__name__).info("Configuration GHT SLS...")

INSTALLED_APPS += [
    "dem",
    "drachar",
    "marche",
    "geprete",
    "finance",
    # 'dra94.apps.Dra94Config',
]

ADMINS = (
    ("NORD Brice", "nord.brice@chu-amiens.fr"),
    ("KLIGLICH Romuald", "kliglich.romuald@chu-amiens.fr"),
    ("JABORSKA Alexandre", "jaborska.alexandre@chu-amiens.fr"),
)

MANAGERS = ADMINS

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "6guuszns@27m*m#nqtih2^rg!b9sh15#&xnc$i!-*fm#@-q@x9"

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]


# Un thème BIOM_AID définit le thème graphique et la mise en page générale d'une page BIOM_AID
# Cela consiste essentiellement en un template de base, qui doit proposer certains emplacements ('blocks') aux vues
# On peut aussi avoir des templates 'configurables' et les variables du thème sont utilisées pour faire cette configuration
BIOM_AID_THEMES = {
    "default": {
        "base_template": "common/base.html",
    },
    "vp": {
        "base_template": "common/base_compact.html",
        "css": "compact.css",
    },
}

# Liste des rôles ayant le droit de créer une demande de matériel
DEM_DEMANDE_CREATION_ROLES = (
    "RMA",
    "CAD",
    "RUN",
    "CHS",
    "CADS",
    "AMAR",
    "DRP",
    "CAP",
    "CSP",
    "ACHP",
    "CHP",
    "COP",
    "DIR",
    "EXP",
    "TECH",
    "P-EXP",  # Expert potentiel = Peut être expert sur l'axe considéré
)


def global_status_message_func(params: dict, campagne_cls: "dem.campagne"):
    from dem.utils import user_campagnes
    from common.models import User

    if isinstance(params["user"], User):
        qs = user_campagnes(params).values()
        if len(qs) > 0:
            return _(
                "La campagne de recensement pour le <b>{nom}</b> se termine le <b>{date}</b>."
            ).format(
                date=qs[0]["fin_recensement"].strftime("%d/%m/%Y"), nom=qs[0]["nom"]
            )
        else:
            return "Pas de campagne de plan courant en cours"
    else:
        return ""


def user_status_message_func(
    params: dict, demande_cls: "dem.demande", userufrole_cls: "common.userufrole"
):
    if params["user"].pk is None:
        return ""
    tmp_scope = userufrole_cls.objects.filter(
        user=params["user"],
        role_code__in=DEM_DEMANDE_CREATION_ROLES,
    )
    nb = demande_cls.objects.filter(
        Q(gel__isnull=True) | Q(gel=False),
        Q(uf__in=tmp_scope.values("uf"))
        | Q(uf__service__in=tmp_scope.values("service"))
        | Q(uf__centre_responsabilite__in=tmp_scope.values("centre_responsabilite"))
        | Q(uf__pole__in=tmp_scope.values("pole"))
        | Q(uf__site__in=tmp_scope.values("site"))
        | Q(uf__etablissement__in=tmp_scope.values("etablissement")),
    ).count()
    return "<b>{}</b> demandes en cours (sur mes UF)".format(nb)


# Un portail BIOM_AID est un système de navigation (essentiellement un menu principal et une page d'accueil)
# qui permet d'accéder à une sélection de vues de BIOM_AID.
# Chaque application 'process" de BIOM_AID intègre son portail (demandes, drachar, marche...) mais il est possible de définir
# des portails spécifiques, par exemple pour intégrer toutes les fonctionnalités destinées à une thématique (travaux, informatique)
# ou à une catégorie particulière d'utilisateurs (services de soins...)
# Choses qu'on peut définir sur un portail :
# - home: page d'accueil et (éventuellement) ses contenus
# - global-status-message : Message d'état global (identique pour tous les utilisateurs), dynamique
# - user-status-message : Message d'état spécifique à l'utilisateur, dynamique
# - main-menu : Menu principal, et ses éventuelles entrées dynamiques (sous-menus)
BIOM_AID_PORTALS = {
    "geqip": {
        "permissions": (
            "RMA",
            "CAD",
            "RUN",
            "CHS",
            "CADS",
            "AMAR",
            "DRP",
            "CAP",
            "CSP",
            "ACHP",
            "CHP",
            "COP",
            "DIR",
            "EXP",
            "DIS",
            "ARB",
            "ADM",
            "TECH",
        ),
        "label": _("Portail GÉQIP : Equipements"),
        "main-name": "GÉQIP",
        "home": "dem:home",
        "global-status-message": global_status_message_func,
        # 'main-status-message': lambda params:_("I'm {user.first_name} {user.last_name}").format(**params),
        "user-status-message": user_status_message_func,
        "home-contents": "cockpit.geqip.dem",
        # Mettre ici les différentes 'tuiles' de la page d'accueil (ou tout autre système de page d'accueil / tableau de bord
        #  à définir...)
        "external-menu": ("intranet", "annuaire", "asset-web"),
        "main-menu": (
            {
                "label": _("Accueil"),
                "url_name": "dem:home",
            },
            {
                "label": _("Nouvelle demande"),
                "help_text": _(
                    "Choisir un sous-menu pour saisir une nouvelle demande d'équipement."
                ),
                "permissions": DEM_DEMANDE_CREATION_ROLES,
                # 'show-only-if-allowed': True,
                "entries": [
                    {
                        "engine": "campagnes",
                    },
                ],
            },
            {
                "label": _("Demandes à approuver"),
                "url_name": "dem:demandes-a-approuver",
                "help_text": _(
                    "Toutes les demandes qui ne sont pas encore approuvées par le chef de pôle ou le directeur"
                ),
            },
            {
                "label": _("Demandes à l'étude"),
                "url_name": "dem:demandes-a-l-etude",
                "help_text": _(
                    "Toutes les demandes qui sont en cours d'étude par les experts (chiffrage, etc.) ou en attente d'arbitrage"
                ),
            },
            {
                "label": _("Demandes acceptées"),
                "url_name": "drachar:suivi-plans",
                "help_text": _(
                    "Suivi des acquisitions (état d'avancement et calendrier prévisionnel) pour toutes les demandes acceptées"
                ),
            },
            {
                "label": _("Demandes archivées"),
                "url_name": "dem:demandes-tout",
                "help_text": _(
                    "Archives de toutes les demandes : Refusées ou acceptées et complètement traitées, etc."
                ),
            },
        ),
    },
    "geqip_ges": {
        "permissions": (
            "GES",
            "ACH",
            "TECH",
        ),
        "label": _("Portail GÉQIP : Commandes & gestion"),
        "main-name": "GÉQIP-G",
        "home": "finance:home",
        "global-status-message": "",
        # 'main-status-message': lambda params:_("I'm {user.first_name} {user.last_name}").format(**params),
        "user-status-message": "",
        "home-contents": {
            # Mettre ici les différentes 'tuiles' de la page d'accueil (ou tout autre système de page d'accueil / tableau de bord
            #  à définir...)
        },
        "external-menu": ("intranet", "annuaire", "asset-web"),
        "main-menu": (
            {
                "label": _("Accueil"),
                "url_name": "finance:home",
            },
            {
                "label": _("Commandes"),
                "entries": (
                    {
                        "label": _("Recherche"),
                        "url_name": "finance:order",
                    },
                    {
                        "label": _("Liste des commandes"),
                        "url_name": "finance:orders",
                    },
                ),
            },
            {
                "label": _("Marchés"),
                "entries": (
                    {
                        "label": _("Asset Plus"),
                        "url_name": "assetplus:marche",
                    },
                ),
            },
            {
                "label": _("Exceptions Marchés"),
                "url_name": "marche:exception_marche",
            },
            {
                "label": _("Factures"),
                "url_name": "finance:invoices",
            },
        ),
    },
    "kos_bo": {
        "main-name": "KOS-BO",
        "permissions": (
            "ADM",
            "EXP",
            "DIS",
            "ARB",
        ),
        "label": _("Portail KOS : Back Office"),
        "theme-name": "kos",
        "home": "dem:tvx-home",
        "external-menu": ("intranet", "annuaire"),
        "main-menu": (
            {
                "label": _("Accueil"),
                "url_name": "dem:tvx-home",
            },
            {
                "label": _("Nouvelle demande"),
                "help_text": _(
                    "Choisir un sous-menu pour saisir une nouvelle demande de travaux."
                ),
                "permissions": DEM_DEMANDE_CREATION_ROLES,
                # 'show-only-if-allowed': True,
                "entries": [
                    {
                        "engine": "campagnes_tvx",
                    },
                ],
            },
            # {
            #     'label': _("Nouvelle demande"),
            #     'permissions': (
            #         'CSP',
            #         'CHP',
            #         'AMAR',
            #         'CAP',
            #         'DIR',
            #         'EXP',
            #     ),
            #     # 'show-only-if-allowed': True,
            #     'entries': {
            #         'engine': 'queryset',
            #         'model': 'dem.calendrier',
            #         'filters': lambda params: {
            #             'debut_recensement__lt': params['now'],
            #             'fin_recensement__gt': params['now'],
            #             'code__contains': 'TVX',
            #         },
            #         'mapping': {
            #             'label': F('nom'),
            #             'url_name': Value('dem:tvx-demande-create'),
            #             # 'url_kwargs': JSONObject(campagne=F('code')),
            #             'url_parameters': JSONObject(choices={'calendrier': F('pk')}),
            #         },
            #     },
            # },
            {
                "label": _("Toutes les demandes en cours"),
                "permissions": (
                    "DIS",
                    "EXP",
                    "ARB",
                ),
                "show-only-if-allowed": True,
                "url_name": "dem:tvx-demande-tech",
            },
            {
                "label": _("Pré-analyse"),
                "permissions": ("DIS",),
                "show-only-if-allowed": True,
                "url_name": "dem:tvx-pre-analyse",
            },
            {
                "label": _("Analyse"),
                "permissions": ("EXP",),
                "show-only-if-allowed": True,
                "url_name": "dem:tvx-analyse",
            },
            {
                "label": _("Validation demandes"),
                "permissions": ("ARB",),
                "show-only-if-allowed": True,
                "url_name": "dem:tvx-demande-validation",
            },
            {
                "label": _("Suivi"),
                "permissions": ("EXP",),
                "show-only-if-allowed": True,
                "url_name": "drachar:suivi-travaux-exp",
            },
            {
                "label": _("Demandes archivées"),
                "permissions": (
                    "EXP",
                    "CSP",
                    "CHP",
                    "AMAR",
                    "CAP",
                    "DIR",
                ),
                "show-only-if-allowed": True,
                "url_name": "dem:tvx-demandes-archivees",
            },
        ),
    },
    "kos": {
        "permissions": (
            "CAD",
            "CHS",
            "CADS",
            "AMAR",
            "DRP",
            "CAP",
            "CSP",
            "ACHP",
            "CHP",
            "COP",
            "DIR",
            "EXP",
            "DIS",
            "ARB",
            "ADM",
        ),
        "main-name": "KOS",
        "label": _("Portail KOS : Travaux courants"),
        "theme-name": "kos",
        "home": "dem:tvx-home",
        "home-contents": {
            # Mettre ici les différentes 'tuiles' de la page d'accueil (ou tout autre système de page d'accueil / tableau de bord
            #  à définir...)
        },
        "external-menu": ("intranet", "annuaire"),
        "main-menu": (
            {
                "label": _("Accueil"),
                "url_name": "dem:tvx-home",
            },
            {
                "label": _("Nouvelle demande"),
                "help_text": _(
                    "Choisir un sous-menu pour saisir une nouvelle demande de travaux."
                ),
                "permissions": DEM_DEMANDE_CREATION_ROLES,
                # 'show-only-if-allowed': True,
                "entries": [
                    {
                        "engine": "campagnes_tvx",
                    },
                ],
            },
            # {
            #     'label': _("Nouvelle demande"),
            #     'permissions': (
            #         'CAD',
            #         'RUN',
            #         'CHS',
            #         'CADS',
            #         'AMAR',
            #         'DRP',
            #         'CAP',
            #         'CSP',
            #         'ACHP',
            #         'CHP',
            #         'COP',
            #         'DIR',
            #         'EXP',
            #         'DIS',
            #         'ARB',
            #         'ADM',
            #     ),
            #     # 'show-only-if-allowed': True,
            #     'entries': {
            #         'engine': 'queryset',
            #         'model': 'dem.calendrier',
            #         'filters': lambda view_params: {
            #             'debut_recensement__lt': view_params['now'],
            #             'fin_recensement__gt': view_params['now'],
            #             'code__contains': 'TVX',
            #         },
            #         'mapping': {
            #             'label': F('nom'),
            #             'url_name': Value('dem:tvx-demande-create'),
            #             # 'url_kwargs': JSONObject(campagne=F('code')),
            #             'url_parameters': JSONObject(choices=Concat(Value('{"calendrier":'), F('pk'), Value('}'))),
            #         },
            #     },
            # },
            {
                "label": _("Demandes à approuver"),
                "permissions": (
                    "CAD",
                    "RUN",
                    "CHS",
                    "CADS",
                    "AMAR",
                    "DRP",
                    "CAP",
                    "CSP",
                    "ACHP",
                    "CHP",
                    "COP",
                    "DIR",
                    "EXP",
                    "DIS",
                    "ARB",
                    "ADM",
                ),
                # 'show-only-if-allowed': True,
                "url_name": "dem:tvx-demande-approb",
            },
            {
                "label": _("Demandes à l'étude"),
                "permissions": (
                    "CAD",
                    "RUN",
                    "CHS",
                    "CADS",
                    "AMAR",
                    "DRP",
                    "CAP",
                    "CSP",
                    "ACHP",
                    "CHP",
                    "COP",
                    "DIR",
                    "EXP",
                    "DIS",
                    "ARB",
                    "ADM",
                ),
                # 'show-only-if-allowed': True,
                "url_name": "dem:tvx-demande",
            },
            {
                "label": _("Demandes acceptées"),
                "permissions": (
                    "CAD",
                    "RUN",
                    "CHS",
                    "CADS",
                    "AMAR",
                    "DRP",
                    "CAP",
                    "CSP",
                    "ACHP",
                    "CHP",
                    "COP",
                    "DIR",
                    "EXP",
                    "DIS",
                    "ARB",
                    "ADM",
                ),
                "show-only-if-allowed": True,
                "url_name": "drachar:suivi-travaux",
            },
            {
                "label": _("Demandes archivées"),
                "permissions": (
                    "CAD",
                    "RUN",
                    "CHS",
                    "CADS",
                    "AMAR",
                    "DRP",
                    "CAP",
                    "CSP",
                    "ACHP",
                    "CHP",
                    "COP",
                    "DIR",
                    "EXP",
                    "DIS",
                    "ARB",
                    "ADM",
                ),
                "show-only-if-allowed": True,
                "url_name": "dem:tvx-demandes-archivees",
            },
        ),
    },
}

BIOM_AID_CONFIGS = {
    # La configuration avec le code None est la configuration  par défaut
    # Le nom d'une config NE DOIT PAS conternir de '-'
    # Une configuration (en attendant un meilleur nom...) est
    "chuap": {
        "default-theme": "default",
        "base_template": "common/base.html",
        "main_project_name": _("GÉQIP"),
        "main_project_title": _("Gestion des Équipements"),
        "external_menu": {
            "ugap": {
                "icon": None,
                "label": _("UGAP"),
                "help_text": _("Accès direct au portail internet de l'UGAP"),
                "url": "https://www.ugap.fr",
                "new_page": True,
            },
        },
        "themes": {
            "default": {"css": None},
            "kos": {"css": "/local/css/kos.css"},
            "vp": {"css": "/common/css/compact-layout.css"},
        },
        # _stmpl = Static Template => calculé à l'initialisation (une fois pour toutes au lancement)
        "persistent_help_stmpl": _(
            """<p><b>GÉQIP <span class="footer-version">V{{dem_version}} ({{dem_version_date}})</span></b> est un
 jeune logiciel en cours de création par le Département Biomédical. Ses développeurs font leur possible pour vous apporter un
 logiciel fiable et complet. N'hésitez pas à nous contacter si vous observez des problèmes. <em>En cas de question ou pour toute
 assistance, les concepteurs se tiennent à votre disposition : </em><span style="display:inline-block; white-space:nowrap;">
 <i class="fa fa-chevron-circle-right" style="padding-left: 1em;"></i> Brice Nord - 88568 -
 <a href="mailto:nord.brice@chu-amiens.fr">nord.brice@chu-amiens.fr</a></span>
 <span style="display:inline-block; white-space:nowrap;"><i class="fa fa-chevron-circle-right" style="padding-left: 1em;">
 </i> Romuald Kliglich - 88561 - <a href="mailto:kliglich.romuald@chu-amiens.fr">kliglich.romuald@chu-amiens.fr</a></span>
 <span style="display:inline-block; white-space:nowrap;"><i class="fa fa-chevron-circle-right" style="padding-left: 1em;"></i>
 Alexandre Jaborska - <a href="mailto:jaborska.alexandre@chu-amiens.fr">jaborska.alexandre@chu-amiens.fr</a></span></p>"""
        ),
        "organisation": 1,  # C'est le code (et non l'id) qu'il faut utiliser
        "external-links": {
            "ugap": {
                "icon": None,
                "label": _("UGAP"),
                "help_text": _("Accès direct au portail internet de l'UGAP"),
                "url": "https://www.ugap.fr",
                "new_page": True,
            },
            "intranet": {
                "icon": None,
                "label": _("Portail Institutionnel"),
                "help_text": _(
                    "Accès (dans un nouvel onglet) à l'intranet du CHU Amiens-Picardie"
                ),
                "url": "https://portail.chu-amiens.fr/",
                "new_page": True,
            },
            "annuaire": {
                "icon": None,
                "label": _("Annuaire"),
                "help_text": _(
                    "Accès (dans un nouvel onglet) à l'annuaire du CHU Amiens-Picardie"
                ),
                "url": "https://portail.chu-amiens.fr/sites/annuaire2",
                "new_page": True,
            },
            "asset-web": {
                "icon": None,
                "label": _("Asset+ WEB"),
                "help_text": _(
                    "Accès (dans un nouvel onglet) à la GMAO Asset Plus Web"
                ),
                "url": "http://piment.chu-amiens.local:8080/AssetPlusWeb/loginView.do",
                "new_page": True,
            },
        },
    },
    "chuaptvx": {
        "based_on": "chuap",
        "main_project_name": _("KOS"),
        "main_project_title": _("Gestion des demandes de travaux courants"),
        "default-theme": "kos",
    },
    "vp": {
        "based_on": "chuap",
        "base_template": "common/base_compact.html",
    },
}

# Si True, toutes les urls doivent commencer par un /url_prefix/ qui est répercuté dans toutes les URL d'un même portail
# Ce préfixe serait sous la forme portail-configuration(-thème). Le thème est facultatif (chaque configuration donne un thème par
#   défaut).
#               ******** A LA DATE DU 17 MAI 2021, BIOM_AID_USE_PREFIX = True NE FONCTIONNE PAS ******
#               ******** ET LES TESTS NE SONT PAS PREVUS POUR POUVOIR TESTER CETTE OPTION ******
#
BIOM_AID_USE_PREFIX = True

DRA94_CFG = {
    "data_path": "users_gmao/achat/",
}

"""_______________________________PARAMETRES POUR LA GMAO________________________________"""


def lien_gmao():  # Récupération des modes de configuration manuel ou auto d'enregistrement avec fichier externe de config
    config = configparser.RawConfigParser()
    module_dir = os.path.dirname(__file__)
    file_path = os.path.join(module_dir, "conf.ini")  # full path to text.
    config.read(file_path)
    param_lien = {
        "link_marque": config.get("GMAOLINK", "link_marque"),
        "link_type": config.get("GMAOLINK", "link_type"),
        "link_compte": config.get("GMAOLINK", "link_compte"),
    }
    return param_lien


def correspondance_assetplus():  # correspondance des tables Asset+ avec les models de BIOM_AID.0
    config = configparser.RawConfigParser()
    module_dir = os.path.dirname(__file__)
    file_path = os.path.join(module_dir, "conf.ini")  # full path to text.
    config.read(file_path)
    param_asset = {
        "Marque": config.get("CORRESPONDANCEASSETPLUS", "Marque"),
        "Type": config.get("CORRESPONDANCEASSETPLUS", "type"),
        "Fournisseur": config.get("CORRESPONDANCEASSETPLUS", "fournisseur"),
        "Inventaire": config.get("CORRESPONDANCEASSETPLUS", "inventaire"),
        "Compte": config.get("CORRESPONDANCEASSETPLUS", "compte"),
        "Cneh": config.get("CORRESPONDANCEASSETPLUS", "cneh"),
    }
    return param_asset


def model_de_gmao():  # Récupération le modèle de GMAO exploitée
    config = configparser.RawConfigParser()
    module_dir = os.path.dirname(__file__)
    file_path = os.path.join(module_dir, "conf.ini")  # full path to text.
    config.read(file_path)
    param_gmao = {
        "model_de_gmao": config.get("GMAOTYPE", "model_de_gmao"),
        "app_gmao": config.get("GMAOTYPE", "model_de_gmao") + "connect",
        "version_de_gmao": config.get("GMAOTYPE", "version_de_gmao"),
    }
    return param_gmao


def local_discipline():  # Récupération le modèle de GMAO exploitée
    config = configparser.RawConfigParser()
    module_dir = os.path.dirname(__file__)
    file_path = os.path.join(module_dir, "conf.ini")  # full path to text.
    config.read(file_path)
    param_discipline = {
        "BM": config.get("LOCALDISCIPLINE", "BM"),
        "BE": config.get("LOCALDISCIPLINE", "BE"),
        "BI": config.get("LOCALDISCIPLINE", "BI"),
        "ST": config.get("LOCALDISCIPLINE", "ST"),
        "EQ": config.get("LOCALDISCIPLINE", "EQ"),
        "IT": config.get("LOCALDISCIPLINE", "IT"),
        "LI": config.get("LOCALDISCIPLINE", "LI"),
        "LO": config.get("LOCALDISCIPLINE", "LO"),
        "DE": config.get("LOCALDISCIPLINE", "DE"),
        "RE": config.get("LOCALDISCIPLINE", "RE"),
        "SI": config.get("LOCALDISCIPLINE", "SI"),
        "CQ": config.get("LOCALDISCIPLINE", "CQ"),
        "99": config.get("LOCALDISCIPLINE", "99"),
        "AM": config.get("LOCALDISCIPLINE", "AM"),
        "BB": config.get("LOCALDISCIPLINE", "BB"),
        "SS": config.get("LOCALDISCIPLINE", "SS"),
    }
    return param_discipline


LIEN_GMAO = lien_gmao()
CORRESPONDANCEASSETPLUS = correspondance_assetplus()
GMAOTYPE = model_de_gmao()
LOCALDISCIPLINE = local_discipline()

"""_______________________________PARAMETRES POUR LA GEF________________________________"""


def lien_gef():  # Récupération des modes de configuration manuel ou auto d'enregistrement avec fichier externe de config
    config = configparser.RawConfigParser()
    module_dir = os.path.dirname(__file__)
    file_path = os.path.join(module_dir, "conf.ini")  # full path to text.
    config.read(file_path)
    param_lien = {
        "link_compte": config.get("GEF_LINK", "link_compte"),
        "file_compte": config.get("GEF_LINK", "file_compte"),
        "link_fournisseur": config.get("GEF_LINK", "link_fournisseur"),
        "link_structure": config.get("GEF_LINK", "link_structure"),
        "link_etablissement": config.get("GEF_LINK", "link_etablissement"),
        "file_structure": config.get("GEF_LINK", "file_structure"),
    }
    return param_lien


def fichiers_gef():  # Récupération des modes de configuration manuel ou auto d'enregistrement avec fichier externe de config
    config = TOMLFile("local/config.toml").read()
    config["GEF"]["FILE"]
    param_lien = {}
    return param_lien


def gef_type():  # Récupération le modèle de GMAO exploitée
    config = configparser.RawConfigParser()
    module_dir = os.path.dirname(__file__)
    file_path = os.path.join(module_dir, "conf.ini")  # full path to text.
    config.read(file_path)
    param_gmao = {
        "model_gef": config.get("GEF_TYPE", "model_gef"),
        "app_gef": config.get("GEF_TYPE", "model_gef") + "connect",
        "version_gef": config.get("GEF_TYPE", "version_gef"),
    }
    return param_gmao


def compte_discipline():  # Récupération le modèle de GMAO exploitée
    config = configparser.RawConfigParser()
    module_dir = os.path.dirname(__file__)
    file_path = os.path.join(module_dir, "conf.ini")  # full path to text.
    config.read(file_path)
    # TODO Voir comment gérer les différent N° de gestionnaire inter établissement (bibliothèque et boucle) ?
    param_discipline = dict(config.items("COMPTEDISCPLINE"))
    return param_discipline


LIEN_GEF = lien_gef()
GEFTYPE = gef_type()
COMPTEDISCPLINE = compte_discipline()
