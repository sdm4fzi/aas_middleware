from typing import Union, List, Tuple, Optional


from aas_middleware.model.formatting.aas.aas_model import AAS, Submodel, SubmodelElementCollection


class GeneralInformation(Submodel):
    """
    Submodel to describe the general information of an order.

    Args:
        id (str): The id of the general information.
        description (Optional[str]): The description of the general information.
        id_short (Optional[str]): The short id of the general information.
        semantic_id (Optional[str]): The semantic id of the general information.
        order_id (str): The id of the order.
        priority (int): The priority of the order.
        customer_information (str): The customer information of the order.
    """
    order_id: str
    priority: int
    customer_information: str

class OrderedProduct(SubmodelElementCollection):
    """
    Submodel that describes the product instances of an order with reference to their AAS.

    Args:
        description (Optional[str]): The description of the product instances.
        id_short (Optional[str]): The short id of the product instances.
        semantic_id (Optional[str]): The semantic id of the product instances.
        product_type (str): Product type of the order.
        target_quantity (int): Number of requested product instances
        product_ids (List[str]): Reference to the AAS of the product instances of the order. 
    """
    product_type: str
    target_quantity: int
    product_ids: List[str] = []

class OrderedProducts(Submodel):
    """
    Submodel that describes the product instances of an order with reference to their AAS.

    Args:
        id (str): The id of the product instances.
        description (Optional[str]): The description of the product instances.
        id_short (Optional[str]): The short id of the product instances.
        semantic_id (Optional[str]): The semantic id of the product instances.
        ordered_products (List[OrderedProduct]): The list of ordered products specifying the ordered type and the quantity of the product type. .
    """
    ordered_products: List[OrderedProduct]



class OrderSchedule(Submodel):
    """
    Submodel to describe the schedule of an order.

    Args:
        id (str): The id of the order schedule.
        description (Optional[str]): The description of the order schedule.
        id_short (Optional[str]): The short id of the order schedule.
        semantic_id (Optional[str]): The semantic id of the order schedule.
        release_time (str): The release time of the order (ISO 8601 datetime).
        due_time (str): The due time of the order (ISO 8601 datetime).
        target_time (str): The target time of the order (ISO 8601 datetime).
    """
    release_time: str
    due_time: str
    target_time: str

class Order(AAS):
    """
    AAS to describe an order.

    Args:
        id (str): The id of the order.
        description (Optional[str]): The description of the order.
        id_short (Optional[str]): The short id of the order.
        product_instances (ProductInstances): The product instances of the order.
        general_information (GeneralInformation): The general information of the order.
        order_schedule (OrderSchedule): The schedule of the order.
    """
    general_information: GeneralInformation
    order_schedule: Optional[OrderSchedule]
    ordered_products: Optional[OrderedProducts]

