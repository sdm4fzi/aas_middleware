from typing import Type

from pydantic import ValidationError

from aas_pydantic.aas_model import (
    AAS,
    Submodel,
    SubmodelElementCollection,
)


def test_minimal_instantiation():
    aas = AAS(id="test")
    assert aas.id == "test"
    assert aas.id_short == "test"

    aas = AAS(id="test", id_short="test_short")
    assert aas.id == "test"
    assert aas.id_short == "test_short"

    aas = AAS(id_short="test_short")
    assert aas.id == "test_short"
    assert aas.id_short == "test_short"

    try:
        AAS(id="_special_character_start")
        assert False
    except ValidationError:
        pass
    try:
        AAS(id="234_digits_start")
        assert False
    except ValidationError:
        pass

    try:
        AAS(id="")
        assert False
    except ValidationError:
        pass

    submodel = Submodel(id="test")
    assert submodel.id == "test"
    assert submodel.id_short == "test"

    submodel = Submodel(id="test", id_short="test_short")

    assert submodel.id == "test"
    assert submodel.id_short == "test_short"

    submodel = Submodel(id_short="test_short")

    assert submodel.id == "test_short"
    assert submodel.id_short == "test_short"

    try:
        Submodel(id="_special_character_start")
        assert False
    except ValidationError:
        pass

    try:
        Submodel(id="234_digits_start")
        assert False
    except ValidationError:
        pass

    try:
        Submodel(id="")
        assert False
    except ValidationError:
        pass

    try:
        SubmodelElementCollection(id="_special_character_start")
        assert False
    except ValidationError:
        pass

    try:
        SubmodelElementCollection(id="234_digits_start")
        assert False
    except ValidationError:
        pass

    try:
        SubmodelElementCollection(id="")
        assert False
    except ValidationError:
        pass


def test_faulty_aas(faulty_aas: Type[AAS]):
    try:
        faulty_aas(id="test", example_string_value="test")
        assert False
    except ValidationError as e:
        pass
