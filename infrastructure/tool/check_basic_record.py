

class CheckBehaviorRecord:
    def __init__(self):
        print("-------------------Check Behavior Records-------------------")
        generic_code_behavior_list = [
            "reset",
            "restart",
            "start",
        ]
        self.register_behaviors(generic_code_behavior_list, in_code=True)

    def register_behaviors(
            self, behavior_name_list, in_code=False,
            can_piece=False, can_destination=False
    ):
        from .models import Behavior
        from infrastructure.assign.models import ApplyBehavior
        register_behavior_names = Behavior.objects.filter(
            name__in=behavior_name_list).values_list("name", flat=True)
        print("Behavior names registered: ", register_behavior_names)
        not_registered_behaviors = set(
            behavior_name_list) - set(register_behavior_names)
        print("Behavior names not registered: ", not_registered_behaviors)

        for behavior in not_registered_behaviors:
            behavior = Behavior.objects.create(
                name=behavior, in_code=in_code, can_piece=can_piece,
                can_destination=can_destination
            )

            ApplyBehavior.objects.create(
                behavior=behavior
            )
