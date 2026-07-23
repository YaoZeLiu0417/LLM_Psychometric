import pytest

from psychometric_v2.taxonomy import DOMAINS, FACETS, LEGACY_FEATURE_MAP


def test_taxonomy_has_five_domains_and_fifteen_facets() -> None:
    assert len(DOMAINS) == 5
    assert len(FACETS) == 15
    assert {facet.domain_id for facet in FACETS.values()} == set(DOMAINS)


def test_every_legacy_feature_maps_to_one_facet() -> None:
    assert len(LEGACY_FEATURE_MAP) == 15
    assert set(LEGACY_FEATURE_MAP.values()) == set(FACETS)


def test_domain_palette_is_not_one_note() -> None:
    assert len({domain.color for domain in DOMAINS.values()}) == 5


@pytest.mark.parametrize("registry", [DOMAINS, FACETS, LEGACY_FEATURE_MAP])
def test_taxonomy_registries_are_read_only(registry: object) -> None:
    probe_key = "__mutation_probe__"
    try:
        with pytest.raises(TypeError):
            registry[probe_key] = object()  # type: ignore[index]
    finally:
        if isinstance(registry, dict):
            registry.pop(probe_key, None)
