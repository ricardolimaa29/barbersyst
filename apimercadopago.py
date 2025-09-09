import mercadopago


def gerar_link(items):
    sdk = mercadopago.SDK(
        "APP_USR-4903128177112457-090519-a0260d6a7bbbae6b2fc422c9144d5a3d-2674994364")

    # request_options = mercadopago.config.RequestOptions()
    # request_options.custom_headers = {
    #     'x-idempotency-key': '<SOME_UNIQUE_VALUE>'
    # }

    payment_data = {
        "items": items,
        "back_urls": {
            "success": "https://www.google.com",  # URL válida e acessível
            "failure": "https://www.google.com",
            "pending": "https://www.google.com"
        },
        "auto_return": "all",
    }
    result = sdk.preference().create(payment_data)
    payment = result["response"]

    print(payment["init_point"])
    return payment["init_point"]
