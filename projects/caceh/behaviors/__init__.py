"""Behaviors de proyecto del bot CACEH.

El motor localiza estas clases por el `app_label` de la Collection del Behavior
(`projects.caceh`) y las busca aquí por su nombre snake_case. Cada módulo se
expone con ese alias, igual que services/behavior/__init__.py hace con los
genéricos. Se irán agregando conforme se implementan (WP5).
"""
from projects.caceh.behaviors.asigna_partes import (
    AsignaPartesBehavior as asigna_partes,
)
from projects.caceh.behaviors.calcula_salario_diario import (
    CalculaSalarioDiarioBehavior as calcula_salario_diario,
)
from projects.caceh.behaviors.calcula_tabulador import (
    CalculaTabuladorBehavior as calcula_tabulador,
)
from projects.caceh.behaviors.valida_fecha_pasada import (
    ValidaFechaPasadaBehavior as valida_fecha_pasada,
)
from projects.caceh.behaviors.registra_contrato import (
    RegistraContratoBehavior as registra_contrato,
)
from projects.caceh.behaviors.genera_pdf import (
    GeneraPdfBehavior as genera_pdf,
)
from projects.caceh.behaviors.entrega_pdf import (
    EntregaPdfBehavior as entrega_pdf,
)
from projects.caceh.behaviors.reinicia_contrato import (
    ReiniciaContratoBehavior as reinicia_contrato,
)
from projects.caceh.behaviors.default_text import (
    DefaultTextBehavior as default_text,
)
