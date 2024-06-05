from typing import List	
from data_models.sdm_reference_model import procedure, processes, reference_model

def check_attribute_predicate(request: processes.AttributePredicate, offer: processes.AttributePredicate) -> bool:
    """
    Checks if an attribute predicate of a request is compatible with an attribute predicate of an offer.

    Args:
        request (procedure.AttributePredicate): The attribute predicate of the request.
        offer (procedure.AttributePredicate): The attribute predicate of the offer.

    Returns:
        bool: True if the attribute predicate of the request is compatible with the attribute predicate of the offer,
            False otherwise.
    """
    if not (request.attribute_carrier == offer.attribute_carrier and request.general_attribute == offer.general_attribute and request.predicate_type == offer.predicate_type):
        return False
    if request.predicate_type == "equals":
        return request.attribute_value == offer.attribute_value
    elif request.predicate_type == "within_range":
        # TODO: currently not working, since attribute_value is string...
        return request.attribute_value[0] <= offer.attribute_value <= request.attribute_value[1]
    elif request.predicate_type == "requires_to_be":
        # TODO: currently not working, since attribute_value is string...
        return offer.attribute_value >= request.attribute_value

def check_process_attributes(request: processes.ProcessAttributes, offer: processes.ProcessAttributes) -> bool:
    """
    Checks if the process attributes of a request are compatible with the process attributes of an offer.

    Args:
        request (processes.ProcessAttributes): The process attributes of the request.
        offer (processes.ProcessAttributes): The process attributes of the offer.

    Returns:
        bool: True if the process attributes of the request are compatible with the process attributes of the offer,
            False otherwise.
    """
    for request_attribute in request.process_attributes:
        if not any([check_attribute_predicate(request_attribute, offer_attribute) for offer_attribute in offer.process_attributes]):
            return False
    return True

def is_procedure_capable_of_process(procedure: procedure.Procedure, process: processes.Process) -> bool:
    """
    Checks if a procedure is capable of processing a process.

    Args:
        procedure (procedure.Procedure): The procedure to check.
        process (processes.Process): The process to check.

    Returns:
        bool: True if the procedure is capable of processing the process, False otherwise.
    """
    process_attributes = process.process_attributes
    procedure_attributes = procedure.process_attributes
    return check_process_attributes(process_attributes, procedure_attributes)


def check_origin_setup_process_attributes(request: procedure.ProcessAttributes, offer: procedure.ProcessAttributes) -> bool:
    """
    Checks if the process attributes of a request are compatible with the process attributes of an offer.

    Args:
        request (procedure.ProcessAttributes): The process attributes of the request.
        offer (procedure.ProcessAttributes): The process attributes of the offer.

    Returns:
        bool: True if the process attributes of the request are compatible with the process attributes of the offer,
            False otherwise.
    """
    offer_attributes = []
    for offer_attribute in offer.process_attributes:
        if offer_attribute.attribute_carrier == "OriginModule":
            new_attribute = offer_attribute.copy()
            new_attribute.attribute_carrier = "Module"
            offer_attributes.append(new_attribute)
    for request_attribute in request.process_attributes:
        if not any([check_attribute_predicate(request_attribute, offer_attribute) for offer_attribute in offer_attributes]):
            return False
    return True


def check_target_setup_process_attributes(request: procedure.ProcessAttributes, offer: procedure.ProcessAttributes) -> bool:
    """
    Checks if the process attributes of a request are compatible with the process attributes of an offer.

    Args:
        request (procedure.ProcessAttributes): The process attributes of the request.
        offer (procedure.ProcessAttributes): The process attributes of the offer.

    Returns:
        bool: True if the process attributes of the request are compatible with the process attributes of the offer,
            False otherwise.
    """
    offer_attributes = []
    for offer_attribute in offer.process_attributes:
        if offer_attribute.attribute_carrier == "TargetModule":
            new_attribute = offer_attribute.copy()
            new_attribute.attribute_carrier = "Module"
            offer_attributes.append(new_attribute)
    for request_attribute in request.process_attributes:
        if not any([check_attribute_predicate(request_attribute, offer_attribute) for offer_attribute in offer_attributes]):
            return False
    return True

def is_procedure_origin_of_setup(procedure: procedure.Procedure, setup_procedure: procedure.Procedure) -> bool:
    return check_origin_setup_process_attributes(
        request=procedure.process_attributes, 
        offer=setup_procedure.process_attributes
    )

def is_procedure_target_of_setup(procedure: procedure.Procedure, setup_procedure: procedure.Procedure) -> bool:
    return check_target_setup_process_attributes(
        request=procedure.process_attributes, 
        offer=setup_procedure.process_attributes
    )


class Matcher:
    """
    The matcher matches requests to offers.
    """
    def __init__(self, processes: processes.Process, procedures: procedure.Procedure) -> None:
        """
        Initializes the matcher.

        Args:
            reference_model (procedure.ReferenceModel): The reference model to create the matcher from.
        """
        self.processes = processes
        self.procedures = procedures

    @classmethod
    def from_reference_model(cls, reference_model: reference_model.ReferenceModel) -> "Matcher":
        """
        Creates a matcher from a reference model.

        Args:
            reference_model (procedure.ReferenceModel): The reference model to create the matcher from.

        Returns:
            Matcher: The created matcher.
        """
        processes = reference_model.processes
        procedures = reference_model.procedures
        return cls(reference_model)

    def get_matching_procedures(self, request: processes.Process) -> List[procedure.Procedure]:
        """
        Matches a request to offers.

        Args:
            request (processes.Process): The request to match.

        Returns:
            List[processes.Process]: The matched offers.
        """
        offers = []
        for procedure in self.procedures:
            if is_procedure_capable_of_process(procedure, request):
                offers.append(procedure)
        return offers
    
    def get_matching_processes(self, offer: procedure.Procedure) -> List[processes.Process]:
        """
        Matches an offer to requests.

        Args:
            offer (procedure.Procedure): The offer to match.

        Returns:
            List[processes.Process]: The matched requests.
        """
        requests = []
        for process in self.processes:
            if is_procedure_capable_of_process(offer, process):
                requests.append(process)
        return requests