"""
Unit tests for data transformation services.
"""

import pytest

from app.services.data_transformer import (
    _parse_datetime_string,
    _transform_born_at,
    _transform_friends,
    chunk_list,
    transform_animal,
)


class TestDataTransformer:
    """Tests for data transformation functions"""

    def test_transform_animal_complete_data(self):
        """Test transforming complete animal data"""
        input_data = {
            "id": 1,
            "name": "Fluffy",
            "type": "cat",
            "friends": "Buddy,Rex,Whiskers",
            "born_at": "2020-01-15T10:30:00Z",
            "color": "orange",
        }

        result = transform_animal(input_data)

        assert result["id"] == 1
        assert result["name"] == "Fluffy"
        assert result["type"] == "cat"
        assert result["friends"] == ["Buddy", "Rex", "Whiskers"]
        assert result["born_at"] == "2020-01-15T10:30:00+00:00"
        assert result["color"] == "orange"

    def test_transform_animal_minimal_data(self):
        """Test transforming minimal animal data"""
        input_data = {
            "id": 2,
            "name": "Rex",
            "type": "dog",
        }

        result = transform_animal(input_data)

        assert result["id"] == 2
        assert result["name"] == "Rex"
        assert result["type"] == "dog"
        # Fields not present should remain as is or be handled gracefully

    def test_transform_friends_string_input(self):
        """Test transforming friends from string to list"""
        friends_string = "Buddy,Rex,Whiskers"
        result = _transform_friends(friends_string)
        assert result == ["Buddy", "Rex", "Whiskers"]

    def test_transform_friends_empty_string(self):
        """Test transforming empty friends string"""
        result = _transform_friends("")
        assert result == []

    def test_transform_friends_single_friend(self):
        """Test transforming single friend"""
        result = _transform_friends("Buddy")
        assert result == ["Buddy"]

    def test_transform_friends_list_input(self):
        """Test transforming friends when already a list"""
        friends_list = ["Buddy", "Rex"]
        result = _transform_friends(friends_list)
        assert result == ["Buddy", "Rex"]

    def test_transform_born_at_iso_format(self):
        """Test transforming ISO format datetime"""
        iso_date = "2020-01-15T10:30:00Z"
        result = _transform_born_at(iso_date)
        assert result == "2020-01-15T10:30:00+00:00"

    def test_transform_born_at_various_formats(self):
        """Test transforming various datetime formats"""
        test_cases = [
            ("2020-01-15 10:30:00", "2020-01-15T10:30:00"),
            ("2020/01/15 10:30:00", "2020-01-15T10:30:00"),
            ("01-15-2020 10:30:00", "2020-01-15T10:30:00"),
        ]

        for input_date, expected_prefix in test_cases:
            result = _transform_born_at(input_date)
            assert result.startswith(expected_prefix)

    def test_transform_born_at_invalid_format(self):
        """Test transforming invalid datetime format"""
        invalid_date = "invalid-date-format"
        result = _transform_born_at(invalid_date)
        # Should return original value if parsing fails
        assert result == invalid_date

    def test_parse_datetime_string_valid_formats(self):
        """Test parsing various valid datetime formats"""
        valid_formats = [
            "2020-01-15T10:30:00Z",
            "2020-01-15 10:30:00",
            "2020/01/15 10:30:00",
            "01-15-2020 10:30:00",
        ]

        for date_string in valid_formats:
            result = _parse_datetime_string(date_string)
            assert result is not None

    def test_parse_datetime_string_invalid_format(self):
        """Test parsing invalid datetime format"""
        result = _parse_datetime_string("invalid-format")
        assert result is None

    def test_chunk_list_normal_case(self):
        """Test chunking list with normal parameters"""
        data = list(range(10))  # [0, 1, 2, ..., 9]
        chunks = chunk_list(data, 3)

        expected_chunks = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]
        assert chunks == expected_chunks

    def test_chunk_list_exact_division(self):
        """Test chunking list with exact division"""
        data = list(range(6))  # [0, 1, 2, 3, 4, 5]
        chunks = chunk_list(data, 3)

        expected_chunks = [[0, 1, 2], [3, 4, 5]]
        assert chunks == expected_chunks

    def test_chunk_list_empty_list(self):
        """Test chunking empty list"""
        chunks = chunk_list([], 3)
        assert chunks == []

    def test_chunk_list_chunk_size_larger_than_list(self):
        """Test chunking with chunk size larger than list"""
        data = [1, 2, 3]
        chunks = chunk_list(data, 10)
        assert chunks == [[1, 2, 3]]

    def test_chunk_list_chunk_size_one(self):
        """Test chunking with chunk size of 1"""
        data = [1, 2, 3]
        chunks = chunk_list(data, 1)
        assert chunks == [[1], [2], [3]]


class TestAnimalTransformationEdgeCases:
    """Tests for edge cases in animal transformation"""

    def test_transform_animal_none_values(self):
        """Test transforming animal with None values"""
        input_data = {
            "id": 1,
            "name": "Test",
            "type": "cat",
            "friends": None,
            "born_at": None,
        }

        result = transform_animal(input_data)
        assert result["id"] == 1
        assert result["name"] == "Test"
        assert result["type"] == "cat"

    def test_transform_animal_with_extra_fields(self):
        """Test transforming animal with extra fields"""
        input_data = {
            "id": 1,
            "name": "Test",
            "type": "cat",
            "extra_field": "extra_value",
            "another_field": 123,
        }

        result = transform_animal(input_data)
        assert result["id"] == 1
        assert result["name"] == "Test"
        assert result["type"] == "cat"
        assert result["extra_field"] == "extra_value"
        assert result["another_field"] == 123
