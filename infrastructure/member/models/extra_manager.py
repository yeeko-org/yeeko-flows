from typing import TYPE_CHECKING, Any, Dict
from django.db.models import Q


if TYPE_CHECKING:
    from django.db import models
    from django.db.models.query import QuerySet
    from infrastructure.talk.models.models import Interaction
    from infrastructure.talk.models.extra import ExtraValue, Session
    from infrastructure.users.models import User
    from infrastructure.xtra.models import Extra


class ExtraManager:
    _extra_values_data: dict
    sessions: "models.QuerySet[Session]"
    extra_values: "models.QuerySet[ExtraValue]"

    def get_extra_values_data(
            self, refresh=False, session: "Session | None" = None
    ) -> dict[str, str]:
        if hasattr(self, "_extra_values_data") and not refresh:
            return getattr(self, "_extra_values_data", {})

        self._extra_values_data = {}

        if session:
            session_filter = Q(session=session)
        else:
            session_filter = Q(session__active=True)

        extra_values_query = self.extra_values.filter(extra__deleted=False)\
            .filter(Q(session__isnull=True) | session_filter)\
            .select_related("extra")

        without_controller = list(
            extra_values_query.filter(controller_value__isnull=True))
        with_controller = list(
            extra_values_query.filter(controller_value__active=True))

        for extra_value in without_controller + with_controller:
            name = extra_value.extra.name
            value = extra_value.get_value()
            self._extra_values_data[name] = value

        user: "User" = self.user  # type: ignore
        self._extra_values_data.update(user.get_basic_data())

        return self._extra_values_data

    def get_extra_controler(
            self, extra: "Extra",
            value: int | None = None,
            session: "Session | None" = None,
            interaction: "Interaction | None" = None,
            active: bool = True,
    ) -> "ExtraValue | None":
        _session = session or self.get_session()
        is_new = True if value is None else False
        if value is None:
            value = self.extra_values\
                .filter(extra=extra, session=_session).count() + 1
        try:
            extra_controler = self.extra_values.get(
                extra=extra, session=_session, value=value)

        except self.extra_values.model.DoesNotExist:
            if not is_new:
                return
                raise ValueError(
                    "ExtraValue not found for existing value")

            return self.add_extra_value(
                extra, str(value), session=_session, active=active,
                interaction=interaction)

        extra_controler.active = active
        extra_controler.save()
        return extra_controler

    def add_extra_value(
            self, extra: "Extra | None",  value: str | None = None,
            interaction: "Interaction | None" = None,
            session: "Session | None" = None,
            controller: "ExtraValue | None" = None,
            active: bool = False,
            origin: str | None = None, list_by=None
    ) -> "ExtraValue | None":
        if not extra:
            return

        extra_values_kwargs: Dict[str, Any] = {"member": self}
        if extra.has_session:
            extra_values_kwargs["session"] = session or self.get_session()

        if extra.controller:
            extra_values_kwargs["controller"] = controller or self.get_extra_controler(
                extra.controller, session=session, interaction=interaction)

        extra_value, _ = self.extra_values.get_or_create(**extra_values_kwargs)

        extra_value.set_value(value)
        if origin:
            extra_value.origin = origin
        extra_value.list_by = list_by
        extra_value.active = active
        extra_value.save()

        if interaction:
            extra_value.interactions.add(interaction)

        return extra_value

    def get_session(self, refresh=False) -> "Session":
        from infrastructure.talk.models import Session
        if hasattr(self, "_session") and not refresh:
            return getattr(self, "_session")

        self._session, _ = Session.objects.get_or_create(
            member=self, active=True)
        return self._session

    def add_circles(
            self, circles: "list[Extra] | QuerySet[Extra]",
            interaction: "Interaction | None" = None,
            origin: str = "unknown", list_by=None
    ):
        for circle in circles:
            self.add_extra_value(
                circle, None, interaction, origin=origin, list_by=list_by)

    def remove_extra(self, extra: "Extra | None"):
        if not extra:
            return
        self.extra_values.filter(extra=extra).delete()

    def remove_extras(self, extras: "list[Extra] | QuerySet[Extra]"):
        self.extra_values.filter(extra__in=extras).delete()

    def remove_all_extras(self):
        self.extra_values.delete()
