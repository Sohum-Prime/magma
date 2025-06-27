import pytest
from magma import hello

def test_hello():
    assert hello() == "Hello from magma!"
