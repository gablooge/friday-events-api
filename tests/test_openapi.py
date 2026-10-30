import pytest
from django.core.management import call_command
from drf_spectacular.generators import SchemaGenerator


@pytest.fixture
def schema():
    return SchemaGenerator().get_schema(request=None, public=True)


def test_schema_is_valid_openapi_3(tmp_path):
    # --fail-on-warn also fails if drf-spectacular had to guess a type
    call_command("spectacular", "--validate", "--fail-on-warn", "--file", str(tmp_path / "schema.yml"))


def test_create_event_documents_request_201_and_400(schema):
    create = schema["paths"]["/api/events/"]["post"]

    assert create["requestBody"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/EventRequest"
    }
    assert create["responses"]["201"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/Event"
    }
    assert create["responses"]["400"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/EventError"
    }


def test_create_request_has_no_read_only_fields(schema):
    request_schema = schema["components"]["schemas"]["EventRequest"]

    assert "id" not in request_schema["properties"]
    assert "host" not in request_schema["properties"]
    assert set(request_schema["required"]) == {"title", "start_time", "end_time"}


def test_400_error_is_a_list_of_messages_per_field(schema):
    end_time = schema["components"]["schemas"]["EventError"]["properties"]["end_time"]

    assert end_time == {"type": "array", "items": {"type": "string"}}


def test_swagger_ui_page_loads(client):
    response = client.get("/api/docs/")

    assert response.status_code == 200
