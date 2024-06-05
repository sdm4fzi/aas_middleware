from __future__ import annotations
from enum import Enum

from typing import Optional, List, Union, Literal
from click import Option
from pydantic.dataclasses import dataclass

from aas_middleware.model.formatting.aas.aas_model import AAS, Submodel, SubmodelElementCollection

from data_models.sdm_reference_model.procedure import Event, GreenHouseGasEmission

class ProductUseType(str, Enum):
    """
    Enum to describe how a subproduct is used in the product.
    """
    ASSEMBLED = "assembled"
    UNASSEMBLED = "unassembled"
    CONSUMED = "consumed"


class SubProduct(SubmodelElementCollection):
    """
    SubmodelElementCollection to describe a subproduct of a product with reference to its AAS, status informatino and quantity.

    Args:
        description (Optional[str]): The description of the subproduct.
        id_short (Optional[str]): The short id of the subproduct.
        semantic_id (Optional[str]): The semantic id of the subproduct.
        product_type (str): The type of the subproduct.
        product_id (str): The AAS reference of the subproduct.
        status (Literal["assembled", "unassembled"]): The status of the subproduct.
        quantity (int): The quantity of the subproduct(s).
    """
    product_type: str
    product_id: str
    product_use_type: ProductUseType
    quantity: int


class BOM(Submodel):
    """
    Submodel to describe the bill of materials of a product.

    Args:
        id (str): The id of the bill of materials.
        description (Optional[str]): The description of the bill of materials.
        id_short (Optional[str]): The short id of the bill of materials.
        semantic_id (Optional[str]): The semantic id of the bill of materials.
        sub_product_count (Optional[int]): The total number of subproducts (depht 1)
        sub_products (Optional[List[SubmodelElementCollection]]): The list of subproducts contained in the product (depht 1)
    """
    sub_product_count: Optional[int]
    sub_products: Optional[List[SubProduct]]


class ProcessReference(Submodel):
    """
    Submodel to reference process to create a product.

    Args:
        id (str): The id of the process reference.
        description (Optional[str]): The description of the process reference.
        id_short (Optional[str]): The short id of the process reference.
        semantic_id (Optional[str]): The semantic id of the process reference.
        process_id (str): reference to the process to create the product
        alternative_process_ids (Optional[List[str]]): alternative processes to create the product
    """

    process_id: str  # reference to the process to create the product
    alternative_processes_ids: Optional[List[str]]


class ConstructionData(Submodel):
    """
    Submodel to describe the construction data of a product.

    Args:
        id (str): The id of the construction data.
        description (Optional[str]): The description of the construction data.
        id_short (Optional[str]): The short id of the construction data.
        semantic_id (Optional[str]): The semantic id of the construction data.
        cad_file (Optional[str]): IRI to a CAD file of the product.
    """
    cad_file: Optional[str]

class ProductInformation(Submodel):
    """
    Submodel to describe general information of the product.

    Args:
        id (str): The id of the product general information.
        description (Optional[str]): The description of the product general information.
        id_short (Optional[str]): The short id of the product general information.
        semantic_id (Optional[str]): The semantic id of the product general information.
        product_type (str): The type of the product.
        manufacturer (str): The manufacturer of the product.
    """
    product_type: str
    manufacturer: str
    maintenance_manual: Optional[str]
    operating_manual: Optional[str]
    disassembly_manual: Optional[str]
    green_house_gas_emission: Optional[GreenHouseGasEmission]


class TrackingData(Submodel):
    """
    Submodel to describe tracking data of a product.

    Args:
        id (str): The id of the tracking data.
        description (Optional[str]): The description of the tracking data.
        id_short (Optional[str]): The short id of the tracking data.
        semantic_id (Optional[str]): The semantic id of the tracking data.
        execution_log (Optional[List[Event]]): The execution log of the product containing all events of the product.
    """
    execution_log: Optional[List[Event]]


class Product(AAS):
    """
    AAS to describe a product.

    Args:
        id (str): The id of the product.
        description (Optional[str]): The description of the product.
        id_short (Optional[str]): The short id of the product.
        semantic_id (Optional[str]): The semantic id of the product.
        construction_data (Optional[ConstructionData]): The construction data of the product.
        bom (Optional[BOM]): The bill of materials of the product.
        process_reference (Optional[ProcessReference]): The process reference of the product.

    """
    product_information: Optional[ProductInformation]
    construction_data: Optional[ConstructionData]
    bom: Optional[BOM]
    process_reference: Optional[ProcessReference]
    tracking_data: Optional[TrackingData]
