# TODO: implement class that takes a data model and rebuilds it with either direct or indirect references

from pydantic import BaseModel

from aas_middleware.model.data_model import DataModel

class DataModelRebuilder:
    def __init__(self, data_model: DataModel):
        """
        Rebuilds a data model with either direct or indirect references.

        Args:
            data_model (DataModel): The data model to rebuild.
        """
        self.data_model = data_model

    def rebuild_data_model_with_associations(self) -> DataModel:
        """
        Rebuilds all models in the data model with assosiations.

        Returns:
            DataModel: The rebuilt data model.
        """
        new_data_model = DataModel()
        referencing_models = []
        for model in self.data_model.get_contained_models():
            reference_infos_of_model = self.data_model.get_referenced_info(model)
            if not reference_infos_of_model:
                new_data_model.add_model(model)
                continue
            referencing_models.append(model)
        # 1. get at first all data models that are referencing but are not referenced by other data models

    
    def rebuild_data_model_for_AAS_structure(self) -> DataModel:
        """
        Rebuilds the data model for AAS meta model structure by adjusting the associations and references and infering correct AAS types.

        Returns:
            DataModel: The rebuilt data model.
        """
        raise NotImplementedError


    def rebuild_data_model_with_references(self) -> DataModel:
        """
        Rebuilds all models in the data model with references.

        Returns:
            DataModel: The rebuilt data model.
        """
        raise NotImplementedError
