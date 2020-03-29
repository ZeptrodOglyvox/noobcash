# Utilities for functional tests


def assert_json_200(response):
    assert response.content_type == 'application/json'
    assert response.status_code == 200
