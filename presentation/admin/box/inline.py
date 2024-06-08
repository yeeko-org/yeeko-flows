from django.contrib import admin

from infrastructure.assign.models import Assign
from infrastructure.assign.models.condition_rule import ConditionRule
from infrastructure.box.models import Destination


class AssignInline(admin.TabularInline):
    model = Assign
    extra = 0
    show_change_link = True
    fields = [
        "circles",
        "extra",
        "extra_value",
        "is_remove",
        "deleted",
    ]
    classes = ["collapse"]
    raw_id_fields = ("extra", )
    filter_vertical = ("circles", )


class DestinationInline(admin.TabularInline):
    model = Destination
    extra = 0
    show_change_link = True
    fields = [
        "destination_type",
        "piece_dest",
        "behavior",
        "url",
        "addl_params",
        "is_default",
        "order",
        "deleted",
    ]
    classes = ["collapse"]
    raw_id_fields = ("piece_dest", "behavior")


class ConditionRuleInline(admin.TabularInline):
    model = ConditionRule
    extra = 0
    show_change_link = True
    fields = [
        "appear",
        "match_all_rules",
        "match_all_conditions",
        "platforms",
        "circles",
        "extra",
        "extra_values",
        "extra_exists",
        "roles",
        "addl_params",
    ]
    raw_id_fields = ("extra",)
    classes = ["collapse"]
