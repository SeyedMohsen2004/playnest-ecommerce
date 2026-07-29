from drf_spectacular.generators import SchemaGenerator


def test_openapi_contract_documents_redirects_and_excludes_payment_secrets():
    schema = SchemaGenerator().get_schema(request=None, public=True)
    paths = schema["paths"]
    schemas = schema["components"]["schemas"]

    health = paths["/api/v1/health/"]["get"]
    assert set(health["responses"]) == {"200"}
    assert health["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/HealthResponse"
    }
    health_status = schemas["HealthResponse"]["properties"]["status"]
    assert health_status["allOf"] == [
        {"$ref": "#/components/schemas/HealthResponseStatusEnum"}
    ]
    assert schemas["HealthResponseStatusEnum"]["enum"] == ["ok"]

    payment_request = paths["/api/v1/payments/request/"]["post"]
    assert set(payment_request["responses"]) == {"201", "400", "401", "403"}
    assert payment_request["responses"]["201"]["content"]["application/json"][
        "schema"
    ] == {"$ref": "#/components/schemas/Payment"}

    callback = paths["/api/v1/payments/zarinpal/callback/"]["get"]
    assert set(callback["responses"]) == {"302"}
    callback_response = callback["responses"]["302"]
    assert set(callback_response["headers"]) == {"Location"}
    assert "content" not in callback_response
    assert {
        (parameter["in"], parameter["name"]) for parameter in callback["parameters"]
    } == {
        ("query", "Authority"),
        ("query", "Status"),
    }

    legacy_verify = paths["/api/v1/payments/verify/"]["post"]
    assert set(legacy_verify["responses"]) == {"410"}
    assert "requestBody" not in legacy_verify
    assert legacy_verify["responses"]["410"]["content"]["application/json"][
        "schema"
    ] == {"$ref": "#/components/schemas/LegacyPaymentVerificationResponse"}

    payment_fields = schemas["Payment"]["properties"]
    assert {
        "authority",
        "card_hash",
        "gateway_response",
        "gateway_message",
        "status_from_gateway",
    }.isdisjoint(payment_fields)
    assert payment_fields["card_pan"]["type"] == "string"
    assert payment_fields["card_pan"]["nullable"] is True

    order_fields = schemas["Order"]["properties"]
    for field_name in (
        "can_retry_payment",
        "can_cancel",
        "can_edit_shipping_info",
    ):
        assert order_fields[field_name]["type"] == "boolean"

    for field_name in (
        "payment_status",
        "payment_status_label",
        "payment_ref_id",
        "manual_review_message",
    ):
        assert order_fields[field_name]["type"] == "string"
        assert order_fields[field_name]["nullable"] is True

    assert order_fields["status_label"]["type"] == "string"
    assert "nullable" not in order_fields["status_label"]
    assert order_fields["shipping_zone_display"]["type"] == "string"
    assert "nullable" not in order_fields["shipping_zone_display"]

    assert schemas["CartProduct"]["properties"]["main_image"]["nullable"] is True
    assert schemas["OrderItem"]["properties"]["product_image"]["nullable"] is True
