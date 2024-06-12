from infrastructure.box.models import Destination
from django.db.models import QuerySet

from infrastructure.member.models.member import Member


def destination_find(
        destinations: QuerySet[Destination], member: Member,
        platform_name: str, raise_exception: bool = True
) -> Destination | None:

    destinations_list = list(destinations)
    if len(destinations_list) == 1:
        return destinations_list[0]

    default_destination = None

    for destination in destinations:

        if destination.is_default:
            default_destination = destination
            evalue = False
        else:
            evalue = destination.evalue_condition_rules(member, platform_name)

        if evalue:
            return destination

    default_destination = default_destination

    if not default_destination and raise_exception:
        raise ValueError("Destination not found")
    return default_destination
