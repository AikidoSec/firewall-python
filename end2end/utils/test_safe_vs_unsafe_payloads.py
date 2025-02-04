from .make_requests import make_post_request, make_path_var_request


def test_safe_vs_unsafe_payloads(payloads, urls, route="", user_id=None):
    json = True
    if "json" in payloads:
        json = payloads["json"]
    print("Safe req to : (1) " + urls["enabled"])
    make_post_request(urls["enabled"] + route, payloads["safe"], status_code=200, user_id=user_id, json=json)
    print("Safe req to : (0) " + urls["disabled"])
    make_post_request(urls["disabled"] + route, payloads["safe"], status_code=200, user_id=user_id, json=json)
    print("Unsafe req to : (1) " + urls["enabled"])
    make_post_request(urls["enabled"] + route, payloads["unsafe"], status_code=500, user_id=user_id, json=json)
    print("Unsafe req to : (0) " + urls["disabled"])
    make_post_request(urls["disabled"] + route, payloads["unsafe"], status_code=200, user_id=user_id, json=json)


def test_payloads_path_variables(payloads, urls, route=""):
    print("Safe req to : (1) " + urls["enabled"])
    make_path_var_request(urls["enabled"] + route, payloads["safe"], status_code=200)
    print("Safe req to : (0) " + urls["disabled"])
    make_path_var_request(urls["disabled"] + route, payloads["safe"], status_code=200)
    print("Unsafe req to : (1) " + urls["enabled"])
    make_path_var_request(urls["enabled"] + route, payloads["unsafe"], status_code=500)
    print("Unsafe req to : (0) " + urls["disabled"])
    make_path_var_request(urls["disabled"] + route, payloads["unsafe"], status_code=200)
