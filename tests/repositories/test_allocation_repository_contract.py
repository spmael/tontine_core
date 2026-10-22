from allocation_repository_contract import assert_allocation_repository_contract

from tontine.repositories import (
    AllocationRepository,
    InMemoryAllocationRepository,
)


def test_in_memory_allocation_repository_satisfies_adapter_contract() -> None:
    repository = InMemoryAllocationRepository()
    assert isinstance(repository, AllocationRepository)
    assert_allocation_repository_contract(InMemoryAllocationRepository)
