from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from django.db.models.query import QuerySet
    from infrastructure.talk.models.models import Interaction
    from infrastructure.talk.models.extra import ExtraValue
    from infrastructure.users.models import User
    from infrastructure.xtra.models import Extra


class ExtraManager:

    @property
    def extra_vale_query(self):
        from infrastructure.talk.models import ExtraValue
        return ExtraValue.objects.filter(member=self)

    def get_extra_values_data(self, refrest=False) -> dict[str, str]:
        user: "User" = self.user  # type: ignore

        if hasattr(self, "_extra_values_data") and not refrest:
            return getattr(self, "_extra_values_data", {})

        self._extra_values_data = {}
        extra_values_query = self.extra_vale_query\
            .filter(extra__deleted=False)\
            .select_related("extra")

        for extra_value in extra_values_query:
            name = extra_value.extra.name
            value = extra_value.get_value()
            self._extra_values_data[name] = value

        self._extra_values_data["username"] = user.username
        self._extra_values_data["first_name"] = user.first_name
        self._extra_values_data["last_name"] = user.last_name
        self._extra_values_data["email"] = user.email
        self._extra_values_data["phone"] = user.phone
        self._extra_values_data["gender"] = user.gender

        return self._extra_values_data

    def add_extra_value(
            self, extra: "Extra | None",  value: str | None = None,
            interaction: "Interaction | None" = None,
            origin: str = "unknown", list_by=None
    ) -> "ExtraValue | None":
        if not extra:
            return
        # get_or_create sobre un queryset .filter(member=self) NO inyecta member
        # al crear (solo lo usa para el get) y member es null=True: sin defaults
        # la fila nace huérfana (member_id=NULL) y get_extra_values_data nunca la
        # vuelve a ver. Lo fijamos explícito.
        extra_value, _ = self.extra_vale_query.get_or_create(
            extra=extra, defaults={"member": self})

        extra_value.set_value(value)
        extra_value.origin = origin
        extra_value.list_by = list_by
        extra_value.save()

        if interaction:
            extra_value.interactions.add(interaction)

        # Mantener coherente el cache en memoria: si ya se materializó (vía
        # get_extra_values_data), un render posterior en el MISMO request leería
        # el valor viejo —p. ej. un behavior escribe ia_pregunta y la pieza que
        # sigue la pinta vacía—. set_value normaliza (json/contador), por eso
        # releemos con get_value en lugar de usar `value` crudo.
        if hasattr(self, "_extra_values_data"):
            self._extra_values_data[extra.name] = extra_value.get_value()

        return extra_value

    def add_circles(
            self, circles: "list[Extra] | QuerySet[Extra]",
            interaction: "Interaction | None" = None,
            origin: str = "unknown", list_by=None
    ):
        for circle in circles:
            self.add_extra_value(circle, None, interaction, origin, list_by)

    def _invalidate_extra_cache(self):
        # Tras un borrado dejamos que el próximo get_extra_values_data refresque
        # de DB: actualizar in situ no vale la pena para un evento poco frecuente.
        if hasattr(self, "_extra_values_data"):
            del self._extra_values_data

    def remove_extra(self, extra: "Extra | None"):
        if not extra:
            return
        self.extra_vale_query.filter(extra=extra).delete()
        self._invalidate_extra_cache()

    def remove_extras(self, extras: "list[Extra] | QuerySet[Extra]"):
        self.extra_vale_query.filter(extra__in=extras).delete()
        self._invalidate_extra_cache()

    def remove_all_extras(self):
        self.extra_vale_query.delete()
        self._invalidate_extra_cache()
