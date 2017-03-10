"""Tests for monkeys/search.py"""

import pytest

import monkeys.search as search


def test_max_score_set_by_assertions_as_score():
    """
    Ensure that a max score attribute is set on scoring functions
    when using the assertions_as_score decorator.
    """
    @search.assertions_as_score
    def score(x):
        assert True
        assert False
        if x:
            assert x
            
    assert score.__max_score == 3
    
    
def test_max_score_not_set_by_assertions_as_score_on_for():
    """
    Ensure that a max score attribute is left unset on scoring
    functions using for loops when using assertions_as_score.
    """
    @search.assertions_as_score
    def score(x):
        for item in xrange(x):
            assert item
            
    with pytest.raises(AttributeError):
        score.__max_score
        
        
def test_max_score_not_set_by_assertions_as_score_on_while():
    """
    Ensure that a max score attribute is left unset on scoring
    functions using while loops when using assertions_as_score.
    """
    @search.assertions_as_score
    def score(x):
        while True:
            value = x()
            if value is None:
                break
            assert value
            
    with pytest.raises(AttributeError):
        score.__max_score
